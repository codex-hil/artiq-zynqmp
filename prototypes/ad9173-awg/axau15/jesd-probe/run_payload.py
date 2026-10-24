"""Volatile ALINX payload RF test; exclusive board and shared scope leases."""
import argparse,fcntl,hashlib,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('bit',type=Path);p.add_argument('--sha256',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reuse-image',action='store_true');a=p.parse_args()
assert hashlib.sha256(a.bit.read_bytes()).hexdigest()==a.sha256
assert a.output.is_absolute();a.output.mkdir(exist_ok=False,parents=True)
scope_lock=open('/home/codex-hil/.cache/mso4104-C020817.lock','a+');fcntl.flock(scope_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
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
 (a.output/'transport.tcl').write_text(Path(__file__).with_name('transport.tcl').read_text())
 (a.output/'dac-plan.tcl').write_text(Path(__file__).with_name('dac-plan.tcl').read_text())
 run('read','set image_magic 0x41585031\n'+Path(__file__).with_name('read.tcl').read_text())
 for name in ['tone-plan.tcl','payload.tcl']:
  (a.output/name).write_text(Path(__file__).with_name(name).read_text())
 from rf_scope import Scope,validate
 captures={}
 with Scope() as scope:
  (a.output/'scope-before.json').write_text(json.dumps({'saved':scope.saved,'untouched':scope.untouched},indent=2)+'\n')
  with (a.output/'payload.txt').open('w') as log:
   proc=subprocess.Popen(docker+['exec',cid,tool+'xsdb',str(a.output/'payload.tcl')],stdout=log,stderr=subprocess.STDOUT)
   try:
    deadline=time.monotonic()+240
    while proc.poll() is None:
     if time.monotonic()>deadline:raise TimeoutError('RF sequence timeout')
     for label in ['baseline','full','half','zero','recovered','asymmetric','final']:
      if label not in captures and (a.output/f'stage-{label}.ready').exists():
       capture=scope.capture(label)
       (a.output/f'scope-{label}.json').write_text(json.dumps(capture,indent=2)+'\n')
       validate(capture,captures)
       captures[label]=capture
       (a.output/f'stage-{label}.done').touch()
       print('RF_STAGE_PASS',label,{ch:{k:v[k] for k in ['fit_hz','fit_vpp','residual_rms']} for ch,v in capture['channels'].items()},flush=True)
     time.sleep(.1)
    if proc.returncode:raise RuntimeError('Tcl RF test failed; inspect payload.txt')
    if len(captures)!=7:raise RuntimeError('Missing RF stages')
   except BaseException:
    (a.output/'abort').touch()
    try:proc.wait(timeout=40)
    except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=10)
    raise
  after={k:scope.io.query(k+'?') for k in scope.untouched}
  (a.output/'scope-unchanged.json').write_text(json.dumps(after,indent=2)+'\n')
  if after!=scope.untouched:raise RuntimeError('Shared scope configuration changed')
 (a.output/'status.json').write_text(json.dumps({'status':'PHYSICAL_PAYLOAD_RF_SCALING_ZERO_RECOVERY_PASS','bit_sha256':a.sha256,'cable':'210512180081','scope_access':'MSO4104 C020817 CH3/4','dac_access':True,'final_state':'FPGA_payload_0x7fff_internal_DC_off_DAC0_149MHz_DAC1_151MHz_running'},indent=2)+'\n')
except BaseException as error:
 try:
  run('mute',Path(__file__).with_name('mute_payload.tcl').read_text())
 except BaseException as mute_error:
  (a.output/'mute-error.txt').write_text(str(mute_error)+'\n')
 (a.output/'status.json').write_text(json.dumps({'status':'FAIL','error':str(error),'bit_sha256':a.sha256,'scope_access':'MSO4104 C020817 CH3/4','final_state':'inspect program/read/payload logs; RF Tcl attempts zero and SPI mute on failure'},indent=2)+'\n')
 raise
finally:
 r=subprocess.run(docker+['logs',cid],capture_output=True,text=True);(a.output/'server.txt').write_text(r.stdout+r.stderr)
 subprocess.run(docker+['stop','-t','2',cid],stdout=subprocess.DEVNULL)
