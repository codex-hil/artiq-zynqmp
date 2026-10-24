"""Volatile ALINX Phaser/IPbus RF test; exclusive board and shared scope leases."""
import argparse,fcntl,hashlib,json,subprocess,time,sys

from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent.parent/'jesd-probe'))
p=argparse.ArgumentParser();p.add_argument('bit',type=Path);p.add_argument('--sha256',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reuse-image',action='store_true');p.add_argument('--uhal',required=True,type=Path);a=p.parse_args()
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
 (a.output/'transport.tcl').write_text((Path(__file__).parent.parent/'jesd-probe/transport.tcl').read_text())
 (a.output/'dac-plan.tcl').write_text((Path(__file__).parent.parent/'jesd-probe/dac-plan.tcl').read_text())
 run('read','set image_magic 0x41584631\n'+(Path(__file__).parent.parent/'jesd-probe/read.tcl').read_text().replace('PASS_ZERO_PAYLOAD_NO_RF_AMPLITUDE_PROOF','PASS_RF_MUTED_NO_AMPLITUDE_PROOF'))
 run('ethernet',Path(__file__).with_name('eth_read.tcl').read_text())
 from network_test import probe
 print(probe(a.output),flush=True)
 r=subprocess.run([str(a.uhal),'ipbusudp-2.0://192.168.2.241:50001',str(Path(__file__).with_name('addresses.xml').resolve())],capture_output=True,text=True,timeout=60)
 (a.output/'uhal.txt').write_text(r.stdout+r.stderr);r.check_returncode()
 for name in ['tone-plan.tcl','rf.tcl']:
  (a.output/name).write_text(Path(__file__).with_name(name).read_text())
 from rf_scope import Scope,Transport
 from client import Phaser
 c=Phaser();c.mute(True)
 captures={}
 with Scope() as scope:
  (a.output/'scope-before.json').write_text(json.dumps({'saved':scope.saved,'untouched':scope.untouched},indent=2)+'\n')
  with (a.output/'rf.txt').open('w') as log:
   proc=subprocess.Popen(docker+['exec',cid,tool+'xsdb',str(a.output/'rf.tcl')],stdout=log,stderr=subprocess.STDOUT)
   try:
    deadline=time.monotonic()+360
    while proc.poll() is None:
     if time.monotonic()>deadline:raise TimeoutError('RF sequence timeout')
     for label in ['baseline','full','half','zero','recovered','shifted','independent','multitone','multitone_phase','final']:
      if label not in captures and (a.output/f'stage-{label}.ready').exists():
       amplitude={'baseline':0,'full':32767/32768,'half':.5,'zero':0,'recovered':32767/32768,'shifted':32767/32768,'independent':32767/32768,'multitone':.08,'multitone_phase':.08,'final':32767/32768}[label]
       offset=.5e6 if label=='shifted' else 1e6
       amp1=.5 if label=='independent' else amplitude
       if label.startswith('multitone'):
        tones=[(f*1e6,.08,k/10+(.25 if label=='multitone_phase' and k==2 else 0)) for k,f in enumerate([-5,-3,-1,1,3])]
        c.configure([tones,tones])
       else:c.configure([[(-offset,amplitude,0)],[(offset,amp1,0)]])
       c.mute(False)
       capture=scope.capture(label,[(3,150e6-offset),(4,150e6+offset)])
       (a.output/f'scope-{label}.json').write_text(json.dumps(capture,indent=2)+'\n')
       if label.startswith('multitone'):
        from multitone_fit import validate_multitone
        validate_multitone(capture,captures['full'],captures.get('multitone') if label=='multitone_phase' else None)
       for channel,v in capture['channels'].items():
        if label.startswith('multitone'):continue
        expected=150e6+(-offset if channel=='3' else offset)
        assert not v['clipped'],v
        if amplitude==0:assert v['fit_vpp']<.005,v
        else:
         assert abs(v['fit_hz']-expected)<50000,v
         assert v['fit_vpp']>.03 and v['residual_rms']<v['fit_vpp']*.15,v
         if label!='full':
          target=(amplitude if channel=='3' else amp1)/(32767/32768)
          ratio=v['fit_vpp']/captures['full']['channels'][channel]['fit_vpp']
          assert abs(ratio-target)<.06,(channel,ratio,target)
          v['ratio_to_full']=ratio
       (a.output/f'scope-{label}.json').write_text(json.dumps(capture,indent=2)+'\n')
       captures[label]=capture
       (a.output/f'stage-{label}.done').touch()
       print('RF_STAGE_PASS',label,{ch:{k:v[k] for k in ['fit_hz','fit_vpp','residual_rms']} for ch,v in capture['channels'].items()},flush=True)
     time.sleep(.1)
    if proc.returncode:raise RuntimeError('Tcl RF test failed; inspect payload.txt')
    if len(captures)!=10:raise RuntimeError('Missing RF stages')
   except BaseException:
    (a.output/'abort').touch()
    try:proc.wait(timeout=40)
    except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=10)
    raise
  after={k:scope.io.query(k+'?') for k in scope.untouched}
  (a.output/'scope-unchanged.json').write_text(json.dumps(after,indent=2)+'\n')
  if after!=scope.untouched:raise RuntimeError('Shared scope configuration changed')
 with Transport(dict(kind='tcp',host='192.168.2.15',port=4000,timeout=4)) as verify:
  restored={k:verify.query(k+'?') for k in scope.saved}
  (a.output/'scope-restored.json').write_text(json.dumps(restored,indent=2)+'\n')
  if restored!=scope.saved:raise RuntimeError('Scope restoration readback mismatch')
 (a.output/'status.json').write_text(json.dumps({'status':'PHYSICAL_PHASER_IPBUS_RF_FREQUENCY_AMPLITUDE_ZERO_RECOVERY_PASS','bit_sha256':a.sha256,'cable':'210512180081','scope_access':'MSO4104 C020817 CH3/4','dac_access':True,'final_state':'Phaser_DDS_307.2MSps_ASF32767_offsets_minus1_plus1MHz_DAC_main_NCO150MHz_both_RF149_151MHz'},indent=2)+'\n')
except BaseException as error:
 try:
  if 'c' in globals():c.mute(True)
 except BaseException:pass
 try:
  run('mute',(Path(__file__).parent.parent/'jesd-probe/mute_payload.tcl').read_text())
 except BaseException as mute_error:
  (a.output/'mute-error.txt').write_text(str(mute_error)+'\n')
 (a.output/'status.json').write_text(json.dumps({'status':'FAIL','error':str(error),'bit_sha256':a.sha256,'scope_access':'MSO4104 C020817 CH3/4','final_state':'inspect program/read/payload logs; RF Tcl attempts zero and SPI mute on failure'},indent=2)+'\n')
 raise
finally:
 if 'c' in globals():c.close()
 r=subprocess.run(docker+['logs',cid],capture_output=True,text=True);(a.output/'server.txt').write_text(r.stdout+r.stderr)
 subprocess.run(docker+['stop','-t','2',cid],stdout=subprocess.DEVNULL)
