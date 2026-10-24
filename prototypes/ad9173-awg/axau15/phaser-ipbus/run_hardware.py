"""ALINX Phaser/IPbus guarded volatile startup; DDS and DAC initially muted."""
import argparse,fcntl,hashlib,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('bit',type=Path);p.add_argument('--sha256',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reuse-image',action='store_true');p.add_argument('--mdio-only',action='store_true');p.add_argument('--start',action='store_true',help='Start default149/151MHz FPGA tones, no scope required');a=p.parse_args()
assert not (a.start and a.mdio_only)
if a.mdio_only:assert a.reuse_image
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
 r=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240)
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
 (a.output/'transport.tcl').write_text((Path(__file__).parent.parent/'jesd-probe/transport.tcl').read_text())
 (a.output/'dac-plan.tcl').write_text((Path(__file__).parent.parent/'jesd-probe/dac-plan.tcl').read_text())
 if not a.mdio_only:run('read','set image_magic 0x41584631\n'+(Path(__file__).parent.parent/'jesd-probe/read.tcl').read_text().replace('PASS_ZERO_PAYLOAD_NO_RF_AMPLITUDE_PROOF','PASS_RF_MUTED_NO_AMPLITUDE_PROOF'))
 run('ethernet',Path(__file__).with_name('eth_read.tcl').read_text())
 if a.start:
  from client import Phaser
  c=Phaser();c.identify();c.mute(True)
  c.configure([[(-1e6,32767/32768,0)],[(1e6,32767/32768,0)]])
  (a.output/'tone-plan.tcl').write_text(Path(__file__).with_name('tone-plan.tcl').read_text())
  run('start',Path(__file__).with_name('start.tcl').read_text())
  c.mute(False)
  if c.read(0x10)[0]!=511 or c.read(0x11)[0]:raise RuntimeError('Startup link/commit state')
  (a.output/'network.json').write_text(json.dumps({'identity':c.identify(),'held':c.read(0x200,21),'commits':c.read(0x12)[0],'mute':c.read(0x13)[0],'counters':c.read(0x18,3)},indent=2)+'\n')
 (a.output/'status.json').write_text(json.dumps({'status':'PHYSICAL_PHASER_STARTUP_PASS_RF_NOT_MEASURED' if a.start else ('PHYSICAL_MDIO_PASS' if a.mdio_only else 'PHYSICAL_JESD_AND_MDIO_STARTUP_PASS_IPBUS_NOT_TESTED'),'bit_sha256':a.sha256,'cable':'210512180081','scope_access':False,'dac_access':not a.mdio_only,'final_state':'FPGA_DDS149_151MHz_fullscale' if a.start else ('unchanged' if a.mdio_only else 'DAC_muted_Ethernet_on_DDS_initially_muted_or_retained_on_reuse')},indent=2)+'\n')
except Exception as error:
 if a.start:
  try:
   if 'c' in globals():c.mute(True)
  except Exception:pass
  try:run('mute',(Path(__file__).parent.parent/'jesd-probe/mute_payload.tcl').read_text())
  except Exception as mute_error:(a.output/'mute-error.txt').write_text(str(mute_error))
 (a.output/'status.json').write_text(json.dumps({'status':'FAIL','error':str(error),'bit_sha256':a.sha256,'scope_access':False,'final_state':'inspect program/read logs; GPIO cleanup attempted by Tcl'},indent=2)+'\n')
 raise
finally:
 if 'c' in globals():c.close()
 r=subprocess.run(docker+['logs',cid],capture_output=True,text=True);(a.output/'server.txt').write_text(r.stdout+r.stderr)
 subprocess.run(docker+['stop','-t','2',cid],stdout=subprocess.DEVNULL)
