"""Volatile SPI identity probe on the identified AXAU15 cable, under its lease."""
import argparse,fcntl,hashlib,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('bit',type=Path);p.add_argument('--sha256',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reuse-image',action='store_true');a=p.parse_args()
assert hashlib.sha256(a.bit.read_bytes()).hexdigest()==a.sha256
assert a.output.is_absolute();a.output.mkdir(exist_ok=False,parents=True)
lock=open('/home/codex-hil/.cache/alinx-210512180081.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
usb=[p for p in Path('/sys/bus/usb/devices').iterdir() if (p/'serial').exists() and (p/'serial').read_text().strip()=='210512180081'];assert len(usb)==1
u=usb[0];node='/dev/bus/usb/%03d/%03d'%(int((u/'busnum').read_text()),int((u/'devnum').read_text()))
docker=['docker','-H','unix:///run/user/1001/docker-vivado.sock'];tool='/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/'
cid=subprocess.check_output(docker+['run','-d','--rm','--init','--mount','type=bind,src=/srv/codex-hil-data,dst=/srv/codex-hil-data','--mount',f'type=bind,src={node},dst={node}','--workdir',str(a.output),'codex-vivado-runtime:ubuntu22.04',tool+'hw_server','-e','set jtag-port-filter 210512180081'],text=True).strip()
def run(name,script):
 path=a.output/(name+'.tcl');path.write_text(script)
 command=docker+['exec',cid,tool+('vivado' if name=='program' else 'xsdb')]
 if name=='program':command+=['-mode','batch','-source',str(path),'-log',str(a.output/'program.log'),'-nojournal']
 else:command+=[str(path)]
 r=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
 (a.output/(name+'.txt')).write_text(r.stdout)
 print(r.stdout[-2000:]);r.check_returncode()
try:
 time.sleep(3)
 if not a.reuse_image: run('program','''open_hw_manager
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
set_property PROGRAM.FILE {'''+str(a.bit.resolve())+'''} $d
program_hw_devices $d
refresh_hw_device $d
report_property $d
close_hw_target
disconnect_hw_server
close_hw_manager
''')
 run('read',Path(__file__).with_name('read.tcl').read_text())
 (a.output/'status.json').write_text(json.dumps({'status':'PHYSICAL_AD9172_SPI_PASS','bit_sha256':a.sha256,'cable':'210512180081','scope_access':False,'dac_access':True,'final_state':'volatile_spi_probe_running_cs_idle_fourwire_enabled_scratch_restored'},indent=2)+'\n')
except Exception as error:
 (a.output/'status.json').write_text(json.dumps({'status':'FAIL','error':str(error),'bit_sha256':a.sha256,'scope_access':False,'final_state':'inspect program/read logs; GPIO cleanup attempted by Tcl'},indent=2)+'\n')
 raise
finally:
 r=subprocess.run(docker+['logs',cid],capture_output=True,text=True);(a.output/'server.txt').write_text(r.stdout+r.stderr)
 subprocess.run(docker+['stop','-t','2',cid],stdout=subprocess.DEVNULL)
