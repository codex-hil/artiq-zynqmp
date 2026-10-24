"""Isolated ALINX SRAM session. Caller owns board lease through restoration."""
import hashlib
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOLDEN = Path('/srv/codex-hil-data/artiq-zynqmp/artifacts/alinx-phaser-20261024g/phaser_ipbus.bit')
GOLDEN_SHA = '5018618518cab3bab43e02a8c1a81691434db69754ef31abb09686d57b8bfb3f'


class HardwareSession:
    def __init__(self, output):
        self.output = output
        self.docker = ['docker', '-H', 'unix:///run/user/1001/docker-vivado.sock']
        self.tool = '/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/'

    def __enter__(self):
        if subprocess.check_output(['hostname'], text=True).strip() != 'greg-OptiPlex-3070':
            raise RuntimeError('Wrong hardware station')
        usb = [p for p in Path('/sys/bus/usb/devices').iterdir()
               if (p/'serial').exists() and (p/'serial').read_text().strip() == '210512180081']
        if len(usb) != 1:raise RuntimeError('ALINX cable identity missing/ambiguous')
        u = usb[0]
        node = '/dev/bus/usb/%03d/%03d' % (int((u/'busnum').read_text()), int((u/'devnum').read_text()))
        self.cid = subprocess.check_output(self.docker+[
            'run', '-d', '--rm', '--init', '--mount',
            'type=bind,src=/srv/codex-hil-data,dst=/srv/codex-hil-data',
            '--mount', f'type=bind,src={node},dst={node}', '--workdir', str(self.output),
            'codex-vivado-runtime:ubuntu22.04', self.tool+'hw_server',
            '-e', 'set jtag-port-filter 210512180081'], text=True).strip()
        try:
            time.sleep(3)
            for name in ('transport.tcl', 'dac-plan.tcl'):
                (self.output/name).write_text((HERE.parent/'jesd-probe'/name).read_text())
            (self.output/'tone-plan.tcl').write_text((HERE/'tone-plan.tcl').read_text())
        except BaseException:
            subprocess.run(self.docker+['stop', '-t', '2', self.cid], stdout=subprocess.DEVNULL)
            raise
        return self

    def run(self, label, script, vivado=False):
        path = self.output/(label+'.tcl');path.write_text(script)
        command = self.docker+['exec', self.cid, self.tool+('vivado' if vivado else 'xsdb')]
        command += ['-mode', 'batch', '-source', str(path), '-log', str(self.output/(label+'.log')), '-nojournal'] if vivado else [str(path)]
        r = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=240)
        (self.output/(label+'.txt')).write_text(r.stdout)
        print(label, r.stdout[-500:], flush=True)
        r.check_returncode()

    def program(self, bit, sha, label):
        if hashlib.sha256(bit.read_bytes()).hexdigest() != sha:raise ValueError('Bitstream SHA mismatch')
        self.run(label, '''open_hw_manager
connect_hw_server -url localhost:3121
set ts [get_hw_targets -filter {NAME =~ *210512180081}]
if {[llength $ts]!=1} {error "Cable mismatch"}
current_hw_target [lindex $ts 0]
set_property PARAM.FREQUENCY 6000000 [current_hw_target]
open_hw_target
set ds [get_hw_devices]
if {[llength $ds]!=1} {error "Unexpected JTAG chain"}
set d [lindex $ds 0]
if {[get_property PART $d] ne "xcau15p" || [string toupper [get_property IDCODE_HEX $d]] ne "04AC2093"} {error "FPGA identity mismatch"}
set_property PROGRAM.FILE {'''+str(bit.resolve())+'''} $d
program_hw_devices $d
refresh_hw_device $d
report_property $d
close_hw_target
disconnect_hw_server
close_hw_manager
''', vivado=True)

    def warm_start(self, label):
        from client import Phaser
        self.run(label+'-read', 'set image_magic 0x41584631\n'+(HERE.parent/'jesd-probe/read.tcl').read_text())
        self.run(label+'-ethernet', (HERE/'eth_read.tcl').read_text())
        c = Phaser()
        try:
            c.identify();c.mute(True)
            c.configure([[(-1e6, 32767/32768, 0)], [(1e6, 32767/32768, 0)]])
            self.run(label+'-start', (HERE/'start.tcl').read_text())
            c.mute(False)
        finally:c.close()

    def __exit__(self, *args):
        r = subprocess.run(self.docker+['logs', self.cid], capture_output=True, text=True)
        (self.output/'server.txt').write_text(r.stdout+r.stderr)
        subprocess.run(self.docker+['stop', '-t', '2', self.cid], stdout=subprocess.DEVNULL, check=True)
