# SPDX-License-Identifier: LGPL-3.0-or-later
"""Interactive explicit phases under one board and plug lease; no timed cycle."""
import datetime,fcntl,hashlib,json,os,socket,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from check_hw_storage import RestoreReserve,runtime_paths
CLI='/home/codex-hil/.local/bin/hil-plug';ENV=None;R={'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phases':{},'power_commands':[]}
PRIVATE=Path('/home/codex-hil/.local/state/artiq-builds/genesys-cycle-20261101');PRIVATE.mkdir(mode=0o700,exist_ok=False)
def save(): (OUT/'report.json').write_text(json.dumps(R,indent=2)+'\n')
def run(name,args,timeout=30):
 z=subprocess.run(args,capture_output=True,text=True,timeout=timeout,env=ENV)
 d={'code':z.returncode,'stdout':z.stdout,'stderr':z.stderr};R['phases'][name]=d;save();print(name,z.returncode,flush=True);return d
def plug(action):
 R['power_commands'].append(action);save();return run(action,[CLI,action])
def main():
 global ENV
 assert socket.gethostname()=='greg-OptiPlex-3070' and os.getuid()==1001
 with open('/home/codex-hil/.cache/genesys-210383B7F02DA.lock','a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  manifest=json.loads((ROOT/'evidence/trained-observer-integration-2026-10-22/runtime-inputs.json').read_text());files=manifest['files']
  for n,f in files.items():
   if n.startswith('restore_'):assert hashlib.sha256(Path(f['path']).read_bytes()).hexdigest()==f['sha256'],n
  reserve=RestoreReserve(runtime_paths(OUT,ROOT));reserve.__enter__();R['reserve']=reserve.report();save()
  try:
   z=run('reservation',[CLI,'reservation']);assert z['code']==0 and not json.loads(z['stdout']).get('lease'),'Plug busy'
   z=subprocess.run([CLI,'reserve','--owner','genesys-native-explicit-off-on-20261101'],capture_output=True,text=True,check=True)
   token=json.loads(z.stdout)['token'];ENV=dict(os.environ,HIL_PLUG_TOKEN=token)
   fd=os.open(PRIVATE/'token',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
   with os.fdopen(fd,'w') as f:f.write(token)
   run('before-status',[CLI,'status']);run('before-ping',['ping','-n','-c','1','-W','2','192.168.2.3'])
   print('READY_EXPLICIT_PHASES',flush=True)
   for line in sys.stdin:
    phase=line.strip()
    if phase=='OFF':
     assert R['power_commands']==[]
     plug('off');run('off-status',[CLI,'status']);run('off-ping',['ping','-n','-c','2','-W','2','192.168.2.3'],8)
     print('OFF_PHASE_DONE',flush=True)
    elif phase=='ON':
     assert R['power_commands']==['off']
     plug('on');run('on-status',[CLI,'status']);print('ON_PHASE_DONE',flush=True)
    elif phase=='CHECK':
     run('after-ping',['ping','-n','-c','1','-W','2','192.168.2.3'],5)
     run('jtag',['docker','-H','unix:///run/user/1001/docker-vivado.sock','exec','a4f3adefe2bd','/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb','/home/codex-hil/.local/state/artiq-builds/genesys-jtag-readonly-20261101/targets.tcl'],45)
     print('CHECK_DONE',flush=True)
    elif phase=='RESTORE':
     assert R['power_commands']==['off','on']
     reserve.release();R['reserve_released']=True;save()
     port='/dev/serial/by-id/usb-Digilent_Digilent_Adept_USB_Device_210383B7F02D-if01-port0';assert Path(port).exists()
     z=run('restore',[sys.executable,str(ROOT/'scripts/load_rtio_runtime.py'),'--server','tcp:172.17.0.3:3121','--cable','210383B7F02DA','--port',port,'--ps-export',str(Path(files['restore_fsbl']['path']).parents[2]),'--bitstream',files['restore_pl']['path'],'--worker',str(Path(files['restore_worker']['path']).parent),'--cpu0',files['restore_cpu0']['path'],'--output',str(OUT/'normal-load')],300)
     print('RESTORE_DONE',z['code'],flush=True)
    elif phase=='LOG':
     run('runtime-log',['/home/codex-hil/.local/bin/artiq_coremgmt','-D','192.168.2.3','log'],15);print('LOG_DONE',flush=True)
    elif phase=='FINISH':break
    else:print('UNKNOWN_PHASE',flush=True)
  finally:
   reserve.release()
   if ENV:
    z=run('release',[CLI,'release'])
    if z['code']==0:(PRIVATE/'token').unlink()
   R['finished']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
 print('CLAIMS_RELEASED',flush=True)
if __name__=='__main__':main()
