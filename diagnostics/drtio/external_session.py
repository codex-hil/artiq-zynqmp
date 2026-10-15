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
            self.result['optical_tx'] = ('upstream ARTIQ idle/AUX with real TSC/RTIO backend; advertised DOWN' if self.tsc_test else 'upstream ARTIQ idle and AUX replies; no RTIO backend')
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
            return self.observe_aux(master_host)
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
        self.result['status'] = ('EXTERNAL_TSC_LOAD_ACK' if getattr(self,'tsc_test',False) else 'EXTERNAL_AUX_ECHO') if good else 'EXTERNAL_AUX_NOT_CONFIRMED'
        if not good: raise RuntimeError('External AUX echo not confirmed; inspect both UART/master logs')

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
