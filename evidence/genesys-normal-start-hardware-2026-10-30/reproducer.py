import sys,os,json,subprocess,time,re
from pathlib import Path
r=Path('/home/codex-hil/artiq-zynqmp/work/artiq-new-wip');sys.path.insert(0,str(r/'scripts'))
from test_candidate_runtime_hw import lease,preflight,bounded,CABLE
from check_hw_storage import require_runtime_space,runtime_paths,RestoreReserve
out=Path('/home/codex-hil/.local/state/artiq-builds/genesys-cold-normal-hw-20261030');out.mkdir(exist_ok=False)
manifest=json.loads((r/'evidence/trained-observer-integration-2026-10-22/runtime-inputs.json').read_text());files=preflight(manifest)
cli='/home/codex-hil/.local/bin/hil-plug';env=os.environ.copy();z=subprocess.run([cli,'reserve','--owner','artiq-genesys: cold normal runtime 20261030'],capture_output=True,text=True,timeout=25)
if z.returncode:raise RuntimeError(z.stderr or z.stdout)
plug=json.loads(z.stdout);env['HIL_PLUG_TOKEN']=plug['token'];private=out.parent/'genesys-cold-plug-private-20261030.json';fd=os.open(private,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:json.dump(plug,f)
result={'status':'FAIL','hardware_executed':False,'scope':'normal cold-start runtime only','stages':{}};start=time.monotonic()
try:
 with lease() as lock:
  preflight(manifest);require_runtime_space(out,r)
  with RestoreReserve(runtime_paths(out,r)) as reserve:
   reserve.release();result['reserve_released_before_normal_load']=True
   env['GENESYS_LEASE_FD']=str(lock.fileno())
   def run(name,cmd,timeout):
    print(name+' START',flush=True);code,text=bounded(cmd,timeout,env,lock.fileno());(out/(name+'.log')).write_text(text);result['stages'][name]=code
    if code:raise RuntimeError(name+' failed; no retry')
    print(name+' PASS',flush=True)
   result['hardware_executed']=True;ps=Path(files['restore_fsbl']['path']).parents[2];worker=Path(files['restore_worker']['path']).parent
   run('load',[sys.executable,str(r/'scripts/load_rtio_runtime.py'),'--server','tcp:172.17.0.3:3121','--cable',CABLE,'--port','/dev/serial/by-id/usb-Digilent_Digilent_Adept_USB_Device_210383B7F02D-if01-port0','--ps-export',str(ps),'--bitstream',files['restore_pl']['path'],'--worker',str(worker),'--cpu0',files['restore_cpu0']['path'],'--output',str(out/'load')],240)
   ip=json.loads((out/'load/results.json').read_text())['ip'];result['ip']=ip
   text,n=re.subn(r'([\"\']host[\"\']\s*:\s*[\"\'])\d+\.\d+\.\d+\.\d+([\"\'])',lambda m:m[1]+ip+m[2],(r/'examples/device_db_genesys.py').read_text());assert n==1
   db=out/'device-db.py';db.write_text(text)
   run('debug',['/srv/codex-hil-data/artiq-zynqmp/venvs/artiq-host/bin/python',str(r/'scripts/test_rtio_debug_hw.py'),'--ip',ip,'--device-db',str(db),'--artiq-run','/home/codex-hil/.local/bin/artiq_run','--output',str(out/'debug')],240)
   run('ethernet',[sys.executable,str(r/'scripts/test_ethernet_hw.py'),'--ip',ip,'--interface','enp2s0','--output',str(out/'ethernet.json')],90)
   result['status']='PASS'
except Exception as ex:result['error']=str(ex)
finally:
 result['elapsed_seconds']=round(time.monotonic()-start,3);(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 z=subprocess.run([cli,'release'],env=env,capture_output=True,text=True,timeout=25)
 if z.returncode:raise RuntimeError('plug release failed; token retained privately')
 private.unlink();print('PLUG_RELEASED',flush=True)
