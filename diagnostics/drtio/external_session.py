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
        if 'observer_alignment' not in self.mapping['registers']:
            raise ValueError('Observer CSR map required')
        verilog = (bit.parent/'top.v').read_text()
        if "assign sfp_disable = 1'd1;" not in verilog:
            raise ValueError('Hard optical TX disable not verified')
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

    def observe(self):
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
