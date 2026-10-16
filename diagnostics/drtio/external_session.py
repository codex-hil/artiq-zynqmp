"""Bounded Genesys receive-only stage inside the Kasli parent's leases.

LGPL-3.0-or-later. Parent must retain Genesys and all Kasli locks through
prepare/observe/restore. No standalone entry point or persistent writes.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[2]
CABLE = '210383B7F02DA'
XSDB = '/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb'


class ExternalSession:
    def __init__(self, config, output):
        self.config = json.loads(Path(config).read_text())
        self.output = Path(output)
        self.touched = False
        self.result = {'status': 'NOT_RUN', 'restoration': 'NOT_RUN',
                       'optical_tx': 'hard disabled', 'remote_drtio': 'NOT_RUN'}
        c = self.config
        if not c.get('network_interface'): raise ValueError('Explicit restore network interface required')
        for key in ('bitstream', 'csr_map', 'restore_bitstream', 'cpu0', 'device_db',
                    'artiq_python', 'artiq_run'):
            if not Path(c[key]).is_file(): raise ValueError('Missing input: ' + key)
        for name in ('worker32.elf', 'start64.elf'):
            if not (Path(c['worker']) / name).is_file(): raise ValueError('Missing worker')
        if CABLE[:-1] not in c['port']:
            raise ValueError('Genesys UART must identify exact board serial')
        bit = Path(c['bitstream'])
        build = json.loads((bit.parent/'results.json').read_text())
        if build.get('status') != 'PASS': raise ValueError('Unqualified observer bitstream')
        for key, filename in [('bitstream','top.bit'), ('csr_map','csr-map.json')]:
            if hashlib.sha256(Path(c[key]).read_bytes()).hexdigest() != build['sha256'][filename]:
                raise ValueError('Observer artifact hash mismatch: ' + key)
        self.mapping = json.loads(Path(c['csr_map']).read_text())
        self.tsc_test = c.get('mode') == 'external-tsc-down'
        self.recovery_test = bool(c.get('recovery_test',False))
        self.stability_test = bool(c.get('stability_test',False))
        self.dio_test = bool(c.get('dio_test',False))
        if self.recovery_test and not self.dio_test: raise ValueError('Recovery requires qualified physical DIO')
        if self.stability_test and not self.dio_test: raise ValueError('Stability requires physical DIO configuration')
        self.reset_test = bool(c.get('reset_test',False))
        if self.dio_test and not self.reset_test: raise ValueError('DIO requires reset test')
        if self.reset_test and not self.tsc_test: raise ValueError('Reset test requires TSC mode')
        self.external_aux = c.get('mode') in ('external-aux-down','external-tsc-down')
        if not self.external_aux and 'observer_alignment' not in self.mapping['registers']:
            raise ValueError('Observer CSR map required')
        verilog = (bit.parent/'top.v').read_text()
        if not self.external_aux and "assign sfp_disable = 1'd1;" not in verilog:
            raise ValueError('Hard optical TX disable not verified')
        if self.external_aux:
            if 'aux_bridge_busy' not in self.mapping['registers']:
                raise ValueError('External AUX map required')
            if 'assign sfp_disable = (~diagnostic_tx_enable_storage);' not in verilog:
                raise ValueError('Expected gated AUX optical TX')
            elf = Path(c['firmware'])
            fw = json.loads((elf.parent/'results.json').read_text())
            if fw.get('status') != 'PASS' or fw.get('mode') != c['mode']:
                raise ValueError('External-only firmware qualification required')
            if hashlib.sha256(elf.read_bytes()).hexdigest() != fw['elf_sha256']:
                raise ValueError('External firmware hash mismatch')
            if fw['csr_map_sha256'] != build['sha256']['csr-map.json']:
                raise ValueError('External firmware/PL maps differ')
            if self.tsc_test:
                policy = REPO/'diagnostics/drtio/aux_protocol/tsc_ack_policy.h'
                if fw.get('tsc_policy_sha256') != hashlib.sha256(policy.read_bytes()).hexdigest():
                    raise ValueError('Stale/unreviewed TSC acknowledgement policy')
                if 'aux_tsc_load_count' not in self.mapping['registers'] or not re.search(r'reg \[60:0\] \w+coarse_ts',verilog):
                    raise ValueError('Kasli fine3 actual-load satellite map required')
            if self.reset_test:
                policy=REPO/'diagnostics/drtio/aux_protocol/reset_backend.h'
                if not fw.get('reset_backend') or fw.get('reset_policy_sha256') != hashlib.sha256(policy.read_bytes()).hexdigest():
                    raise ValueError('Hardware reset firmware/policy required')
                if fw.get('c_source_sha256') != hashlib.sha256(policy.with_name('firmware.c').read_bytes()).hexdigest():
                    raise ValueError('Stale reset firmware source')
                if not all('aux_'+n in self.mapping['registers'] for n in ('rtio_reset_request','rtio_reset_applied','phy_reset_request','phy_reset_applied')):
                    raise ValueError('Split reset CSRs required')
            if self.dio_test:
                policy=REPO/'diagnostics/drtio/aux_protocol/leaf_policy.h'
                if not fw.get('dio_leaf') or fw.get('leaf_policy_sha256') != hashlib.sha256(policy.read_bytes()).hexdigest():
                    raise ValueError('Qualified leaf readiness required')
                if fw.get('rust_source_sha256') != hashlib.sha256(policy.with_name('lib.rs').read_bytes()).hexdigest():
                    raise ValueError('Stale leaf AUX codec')
            elif fw.get('dio_leaf'):
                raise ValueError('Readiness firmware requires explicit physical DIO test')
            self.result['optical_tx'] = ('upstream ARTIQ idle/AUX with real TSC/RTIO backend; advertised DOWN' if self.tsc_test else 'upstream ARTIQ idle and AUX replies; no RTIO backend')
            if self.dio_test: self.result['optical_tx']='upstream ARTIQ RT/AUX; readiness-gated direct destination1 leaf'
            self.result['firmware_sha256'] = fw['elf_sha256']
        self.result['bit_sha256'] = build['sha256']['top.bit']

    def run(self, name, argv, timeout=240, host=False):
        self.output.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env['GENESYS_LEASE_FD'] = str(self.lease_fd)
        if host: env.pop('PYTHONPATH', None)
        child = subprocess.run(argv, cwd=REPO, capture_output=True, text=True,
            timeout=timeout, env=env, pass_fds=(self.lease_fd,))
        (self.output/(name+'.log')).write_text(child.stdout+child.stderr)
        if child.returncode: raise RuntimeError('External stage failed: ' + name)
        return child.stdout

    def common(self):
        c = self.config
        return ['--server',c['server'],'--cable',CABLE,'--port',c['port'],
                '--ps-export',c['ps_export']]

    def prepare(self, lease_fd):
        self.lease_fd = lease_fd
        expected = Path('/home/codex-hil/.cache/genesys-'+CABLE+'.lock').stat()
        actual = os.fstat(lease_fd)
        if (expected.st_dev, expected.st_ino) != (actual.st_dev, actual.st_ino):
            raise ValueError('Wrong parent Genesys lease')
        self.touched = True
        self.run('load', [sys.executable,str(REPO/'scripts/load_drtio_diagnostic.py'),
            *self.common(), '--bitstream',self.config['bitstream'],
            '--output',str(self.output/'load')])

    def observe(self, master_host=None):
        if getattr(self, 'external_aux', False):
            self.observe_aux(master_host)
            if getattr(self,'recovery_test',False): self.probe_link_recovery(master_host)
            return
        lines = ['lassign $argv server cable', 'connect -url $server', 'set matches {}',
            'foreach p [targets -target-properties -filter {name == "PSU"}] {',
            'if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}',
            '}', 'if {[llength $matches]!=1} {error "Exact Genesys target missing"}',
            'targets -set [lindex $matches 0]', 'configparams force-mem-accesses 1']
        for name, value in self.mapping['registers'].items():
            if value['words'] != 1: raise ValueError('Single-word map required')
            lines.append('set addr('+name+') '+str(value['address']))
        lines.append('''
proc wr {n v} {global addr; mwr $addr($n) $v}
proc rd {n} {global addr; return [expr {wide([mrd -value $addr($n)]) & 0xffffffff}]}
proc sample {} {
 wr monitor_snapshot 1
 set values {}
 foreach n {monitor_status monitor_boot_ticks monitor_rx_ticks monitor_tx_ticks observer_alignment observer_rt_words observer_rt_frames observer_aux_words observer_aux_frames} {
  lappend values [rd $n]
 }
 puts "EXTERNAL_SAMPLE $values"
}
if {[rd monitor_magic]!=0x44525430} {error "Wrong diagnostic PL"}
wr monitor_tx_enable 0
wr monitor_reset 1
wr observer_enable 0
wr monitor_loopback 0
wr monitor_prbs 0
wr monitor_tx_prbs 0
after 50
wr monitor_reset 0
after 2000
wr observer_enable 1
after 100
sample
for {set i 0} {$i<3} {incr i} {after 500; sample}
wr observer_enable 0
wr monitor_tx_enable 0
puts "EXTERNAL_OBSERVATION_COMPLETE"
disconnect
''')
        tcl = self.output/'observe.tcl'
        tcl.write_text('\n'.join(lines)+'\n')
        log = self.run('observe', ['vivado-container','shell','-c','exec "$@"',
            'bash',XSDB,str(tcl),self.config['server'],CABLE], timeout=60)
        samples = [[int(x) for x in line.split()[1:]] for line in log.splitlines()
                   if line.startswith('EXTERNAL_SAMPLE ')]
        self.result['samples'] = samples
        if len(samples)!=4 or 'EXTERNAL_OBSERVATION_COMPLETE' not in log:
            raise RuntimeError('Missing bounded observation samples')
        self.result['scope'] = 'external receive clock/comma observation; not packet/CRC or synchronization proof'
        good = all(len(s)==9 and s[0]&0x7f==0x7f and s[0]&0x80 and not s[0]&0x100 and s[4]&1 for s in samples)
        ratios = []
        for a,b in zip(samples,samples[1:]):
            ticks = (b[1]-a[1]) & 0xffffffff
            if not ticks: good = False; continue
            ratios.append(((b[2]-a[2]) & 0xffffffff)/ticks)
        self.result['rx_boot_ratios'] = ratios
        good = good and len(ratios)==3 and all(.95 < x < 1.05 for x in ratios)
        self.result['status'] = 'RX_CLOCK_AND_COMMA' if good else 'RX_NOT_CONFIRMED'
        if not good: raise RuntimeError('External RX not confirmed; inspect status/LOS/clock/alignment')

    def observe_aux(self, master_host):
        import serial
        if not master_host: raise ValueError('Actual scoped master host required')
        raw = bytearray()
        with serial.Serial(self.config['port'],115200,timeout=.2,exclusive=True) as uart:
            uart.reset_input_buffer()
            self.run('aux-start',[ 'vivado-container','shell','-c','exec "$@"','bash',XSDB,
                str(REPO/'scripts/run_ethernet.tcl'),self.config['server'],
                self.config['firmware'],CABLE],timeout=60)
            start = time.monotonic()
            queried = False
            master = ""
            try:
                while time.monotonic()-start < 25:
                    raw.extend(uart.read(uart.in_waiting or 1))
                    if not queried and time.monotonic()-start > 3:
                        queried = True
                        master = self.run('master-aux-log',[self.config['artiq_python'],
                            '-m','artiq.frontend.artiq_coremgmt','-D',master_host,'log'],
                            timeout=15,host=True)
                    if b'AUX_FW PANIC' in raw or b'ARTIQ_AUX_FIRMWARE FAIL' in raw:
                        raise RuntimeError('External AUX firmware rejected startup')
                if getattr(self,'reset_test',False):
                    if b'AUX_TSC ACK count=1' not in raw or b'AUX_RESET COLD_RELEASE PASS' not in raw:
                        raise RuntimeError('Reset probe requires observed cold release and TSC ACK')
                    self.probe_reset(master_host,uart,raw)
                    if getattr(self,'dio_test',False): self.probe_dio(master_host,uart,raw)
                    if getattr(self,'stability_test',False): self.probe_stability(master_host,uart,raw)
            finally:
                (self.output/'aux-uart.log').write_bytes(raw)
        text = raw.decode(errors='replace')
        echo = text.count('AUX_SERVICE RESPOND request=0 reply=1')
        down = text.count('AUX_SERVICE RESPOND request=32 reply=33')
        self.result.update(echo_replies=echo, destination_down_replies=down,
            firmware_send_errors=text.count('AUX_SERVICE SEND_FAIL'),
            firmware_rx_errors=text.count('AUX_SERVICE RX_ERROR'),
            unsupported_drops=text.count('AUX_SERVICE DROP'),
            master_link_echo_observed=bool(re.search(r'\[LINK#\d+\] remote replied after \d+ packets',master)),
            scope='real external AUX codec/CRC echo and DOWN status, not production satellite',
            tsc_synchronization='NOT_IMPLEMENTED', remote_rtio='NOT_IMPLEMENTED')
        if getattr(self,'tsc_test',False):
            final_master = self.run('master-tsc-log',[self.config['artiq_python'],
                '-m','artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
            link = re.search(r'\[LINK#(\d+)\] remote replied after',master)
            prefix = '[LINK#'+link[1]+']' if link else 'MISSING-LINK'
            counts = [int(n) for n in re.findall(r'AUX_TSC ACK count=(\d+)',text)]
            tsc_ok = ('AUX_TSC BASELINE count=0' in text and counts==[1] and
                'AUX_TSC REJECT' not in text and bool(link) and
                prefix+' failed to sync TSC' not in final_master and
                prefix+' link initialization completed' in final_master)
            self.result.update(tsc_ack_counts=counts, tsc_load_handshake='PASS' if tsc_ok else 'FAIL',
                tsc_synchronization='load/ACK only; offset/jitter/deterministic latency NOT_MEASURED', remote_rtio='NOT_VALIDATED')
        else: tsc_ok=True
        good = tsc_ok and echo > 0 and self.result['master_link_echo_observed'] and not (
            self.result['firmware_send_errors'] or self.result['firmware_rx_errors'])
        if getattr(self,'reset_test',False): good = good and self.result.get('reset_handshake')=='PASS'
        if getattr(self,'dio_test',False):
            good = good and self.result.get('dio_loopback')=='PASS'
            self.result['remote_rtio']='physical TTL output/input PASS'
        self.result['status'] = ('EXTERNAL_DIO_LOOPBACK' if getattr(self,'dio_test',False) else 'EXTERNAL_RESET_ACK' if getattr(self,'reset_test',False) else 'EXTERNAL_TSC_LOAD_ACK' if getattr(self,'tsc_test',False) else 'EXTERNAL_AUX_ECHO') if good else 'EXTERNAL_AUX_NOT_CONFIRMED'
        if not good: raise RuntimeError('External AUX echo not confirmed; inspect both UART/master logs')

    def probe_reset(self,master_host,uart,raw):
        c=self.config
        before=self.run('master-before-reset-log',[c['artiq_python'],'-m',
            'artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
        db={'core':{'type':'local','module':'artiq.coredevice.core','class':'Core',
            'arguments':{'host':master_host,'target':'rv32ima','ref_period':1e-9,'analyzer_proxy':None}}}
        path=self.output/'reset-device-db.py';path.write_text('device_db = '+repr(db)+'\n')
        for i in range(2):
            log=self.run('master-reset-probe-'+str(i),[c['artiq_python'],'-m','artiq.frontend.artiq_run',
                '--device-db='+str(path),'--dataset-db='+str(self.output/'reset-datasets.mdb'),
                str(REPO/'examples/kasli_counter_probe.py')],timeout=30,host=True)
            if 'KASLI_COUNTER_RPC_PASS' not in log:raise RuntimeError('Reset kernel/RPC did not finish')
            end=time.monotonic()+1
            while time.monotonic()<end:raw.extend(uart.read(uart.in_waiting or 1))
        after=self.run('master-after-reset-log',[c['artiq_python'],'-m',
            'artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
        text=raw.decode(errors='replace')
        completed=re.findall(r'AUX_RESET COMPLETE count=(\d+)',text)
        replies=text.count('AUX_SERVICE RESPOND request=2 reply=3')
        # Prior startup probes may have timed out before the responder existed.
        # Compare occurrence counts so those historical errors cannot hide a new one.
        errors=lambda log:len(re.findall(r'\[LINK#\d+\] reset failed',log))
        good=(completed==['1','1'] and replies==2 and 'AUX_RESET REJECT' not in text and
            'AUX_FW PANIC' not in text and errors(after)==errors(before))
        self.result.update(reset_handshake='PASS' if good else 'FAIL',
            reset_completed_load_counts=completed,reset_ack_replies=replies,
            master_reset_errors_before=errors(before),master_reset_errors_after=errors(after),
            reset_scope='two native core.reset kernels; queue reset preserves PHY; no remote TTL or timing-offset proof')
        if not good:raise RuntimeError('External native reset/ACK not confirmed')

    def probe_dio(self,master_host,uart,raw):
        c=self.config
        before=self.run('master-before-dio-log',[c['artiq_python'],'-m',
            'artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
        if '[DEST#1] destination is up' not in before:
            raise RuntimeError('Native master has not enabled destination1; no TTL experiment')
        db={'core':{'type':'local','module':'artiq.coredevice.core','class':'Core',
            'arguments':{'host':master_host,'target':'rv32ima','ref_period':1e-9,'analyzer_proxy':None}}}
        for name,cls,channel in [('ttl_out','TTLOut',0x10000),('ttl_in','TTLInOut',0x10001)]:
            db[name]={'type':'local','module':'artiq.coredevice.ttl','class':cls,
                'arguments':{'channel':channel}}
        path=self.output/'dio-device-db.py';path.write_text('device_db = '+repr(db)+'\n')
        for i in range(2):
            log=self.run('master-dio-probe-'+str(i),[c['artiq_python'],'-m','artiq.frontend.artiq_run',
                '--device-db='+str(path),'--dataset-db='+str(self.output/'dio-datasets.mdb'),
                str(REPO/'examples/kasli_drtio_dio.py')],timeout=45,host=True)
            if not re.search(r'DRTIO_DIO_PASS\s+8\s+100000',log):
                raise RuntimeError('Remote physical DIO result absent')
            end=time.monotonic()+1
            while time.monotonic()<end:raw.extend(uart.read(uart.in_waiting or 1))
        after=self.run('master-after-dio-log',[c['artiq_python'],'-m',
            'artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
        bad=r'reset failed|RTIO (?:sequence|collision|busy) error|failed to sync TSC|timeout attempting to get remote buffer space'
        if len(re.findall(bad,after))!=len(re.findall(bad,before)):
            raise RuntimeError('New master transport/RTIO error during DIO')
        text=raw.decode(errors='replace')
        if any(t in text for t in ('AUX_FW PANIC','AUX_RESET REJECT','AUX_SERVICE SEND_FAIL','AUX_SERVICE RX_ERROR')):
            raise RuntimeError('Satellite firmware fault during DIO')
        self.result.update(dio_loopback='PASS',dio_runs=2,pulses_per_run=8,
            remote_drtio='direct-leaf physical TTL PASS; remaining satellite services incomplete',
            rising_edge_spacing_mu=100000,remote_rtio='physical TTL output/input PASS',
            dio_scope='Kasli standard kernel through external DRTIO to Genesys JB1/JB2; fine3 timestamps,8ns physical resolution; absolute phase/jitter NOT_MEASURED')

    def probe_stability(self,master_host,uart,raw):
        c=self.config
        before=self.run('master-before-stability-log',[c['artiq_python'],'-m',
            'artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
        if '[DEST#1] destination is up' not in before:raise RuntimeError('Stability requires native destination UP')
        for i in range(2):
            log=self.run('master-stability-'+str(i),[c['artiq_python'],'-m','artiq.frontend.artiq_run',
                '--device-db='+str(self.output/'dio-device-db.py'),
                '--dataset-db='+str(self.output/'stability-datasets.mdb'),
                str(REPO/'examples/kasli_drtio_stability.py')],timeout=120,host=True)
            if not re.search(r'DRTIO_STABILITY_PASS\s+2048\s+128',log):
                raise RuntimeError('Missing physical width/spacing stability result')
            end=time.monotonic()+1
            while time.monotonic()<end:raw.extend(uart.read(uart.in_waiting or 1))
        after=self.run('master-after-stability-log',[c['artiq_python'],'-m',
            'artiq.frontend.artiq_coremgmt','-D',master_host,'log'],timeout=15,host=True)
        bad=r'reset failed|RTIO (?:sequence|collision|busy) error|failed to sync TSC|timeout attempting to get remote buffer space'
        if len(re.findall(bad,after))!=len(re.findall(bad,before)):
            raise RuntimeError('New native master error in stability test')
        text=raw.decode(errors='replace')
        if any(t in text for t in ('AUX_FW PANIC','AUX_RESET REJECT','AUX_SERVICE SEND_FAIL','AUX_SERVICE RX_ERROR')):
            raise RuntimeError('Satellite fault in stability test')
        self.result.update(dio_stability='PASS',stability_runs=2,
            stability_edges=4096,stability_pulses=2048,stability_batches=256,
            stability_widths_mu=[800,8000,10000,30000],
            stability_periods_mu=[16000,40000,100000,250000],
            stability_empty_reads=256,stability_native_rtio_resets=8,
            stability_scope='Both physical edge timestamps and widths/periods; no link-loss/retraining or absolute phase proof')

    def probe_link_recovery(self,master_host):
        import serial
        c=self.config
        reg=self.mapping['registers']
        lines=['lassign $argv server cable','connect -url $server','set matches {}',
            'foreach p [targets -target-properties -filter {name == "PSU"}] {',
            'if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}',
            '}','if {[llength $matches]!=1} {error "Exact Genesys target missing"}',
            'targets -set [lindex $matches 0]','configparams force-mem-accesses 1',
            'if {[expr {wide([mrd -value '+str(reg['monitor_magic']['address'])+']) & 0xffffffff}] != 0x44525430} {error "Wrong PL"}',
            'mwr '+str(reg['monitor_reset']['address'])+' 1','after 1000',
            'mwr '+str(reg['monitor_reset']['address'])+' 0',
            'puts "GENESYS_GTH_RESET_RELEASED"','disconnect']
        tcl=self.output/'link-reset.tcl';tcl.write_text('\n'.join(lines)+'\n')
        cycles=[]
        for name in ('master-dio-probe-0.log','master-dio-probe-1.log',
                     'master-before-dio-log.log','master-after-dio-log.log'):
            source=self.output/name
            if source.exists():(self.output/('initial-'+name)).write_bytes(source.read_bytes())
        def master_log(name):
            return self.run(name,[c['artiq_python'],'-m','artiq.frontend.artiq_coremgmt',
                '-D',master_host,'log'],timeout=15,host=True)
        for cycle in range(2):
            before=master_log('master-before-recovery-'+str(cycle))
            raw=bytearray()
            with serial.Serial(c['port'],115200,timeout=.2,exclusive=True) as uart:
                uart.reset_input_buffer()
                try:
                    reset=self.run('link-reset-'+str(cycle),['vivado-container','shell','-c','exec "$@"',
                        'bash',XSDB,str(tcl),c['server'],CABLE],timeout=30)
                    if 'GENESYS_GTH_RESET_RELEASED' not in reset:raise RuntimeError('GTH reset not confirmed')
                    end=time.monotonic()+15
                    while time.monotonic()<end:raw.extend(uart.read(uart.in_waiting or 1))
                    after=master_log('master-after-recovery-'+str(cycle))
                    tokens=['[LINK#0] link is down','[LINK#0] link initialization completed',
                            '[DEST#1] destination is up']
                    if not all(after.count(t)==before.count(t)+1 for t in tokens):
                        raise RuntimeError('Native DOWN/reinitialization/destination-UP cycle absent')
                    text=raw.decode(errors='replace')
                    if len(re.findall(r'AUX_TSC ACK count=1\b',text))!=1 or 'AUX_TSC REJECT' in text:
                        raise RuntimeError('Fresh actual-load TSC ACK absent after GTH reset')
                    bad=r'failed to sync TSC|reset failed|RTIO (?:sequence|collision|busy) error|timeout attempting to get remote buffer space'
                    if len(re.findall(bad,after))!=len(re.findall(bad,before)):
                        raise RuntimeError('New native error after link recovery')
                    self.probe_dio(master_host,uart,raw)
                    # Preserve each cycle's standard experiment/log outputs.
                    for name in ('master-dio-probe-0.log','master-dio-probe-1.log',
                                 'master-before-dio-log.log','master-after-dio-log.log'):
                        (self.output/('recovery-'+str(cycle)+'-'+name)).write_bytes((self.output/name).read_bytes())
                    cycles.append({'cycle':cycle,'status':'PASS','hold_ms':1000,
                        'fresh_tsc_ack':1,'native_down_up':True,'dio_runs':2})
                finally:
                    (self.output/('recovery-uart-'+str(cycle)+'.log')).write_bytes(raw)
        self.result.update(link_recovery='PASS',link_recovery_cycles=cycles,
            link_recovery_scope='Forced volatile Genesys GTH reset, native master link DOWN/new TSC ACK/UP and physical DIO again; no cable removal or absolute phase qualification')

    def restore(self):
        if not self.touched: return
        c = self.config
        try:
            self.run('restore-load', [sys.executable,str(REPO/'scripts/load_rtio_runtime.py'),
                *self.common(),'--bitstream',c['restore_bitstream'],'--worker',c['worker'],
                '--cpu0',c['cpu0'],'--output',str(self.output/'restore-load')])
            ip = json.loads((self.output/'restore-load/results.json').read_text())['ip']
            self.result['restored_ip'] = ip
            text, count = re.subn(r'(["\']host["\']\s*:\s*["\'])\d+\.\d+\.\d+\.\d+(["\'])',
                lambda m:m[1]+ip+m[2], Path(c['device_db']).read_text())
            if not count: raise RuntimeError('No core host in restore device database')
            db = self.output/'device_db.py'; db.write_text(text)
            self.run('restore-debug', [c['artiq_python'],str(REPO/'scripts/test_rtio_debug_hw.py'),
                '--ip',ip,'--device-db',str(db),'--artiq-run',c['artiq_run'],
                '--output',str(self.output/'restore-debug')],host=True)
            self.run('restore-ethernet',[sys.executable,str(REPO/'scripts/test_ethernet_hw.py'),
                '--ip',ip,'--interface',c['network_interface'],
                '--output',str(self.output/'restore-ethernet.json')],timeout=90)
            self.result['restoration'] = 'PASS'
        except Exception as error:
            self.result['restoration'] = 'FAIL'
            self.result['restore_error'] = str(error)
            raise
        finally:
            (self.output/'results.json').write_text(json.dumps(self.result,indent=2)+'\n')
