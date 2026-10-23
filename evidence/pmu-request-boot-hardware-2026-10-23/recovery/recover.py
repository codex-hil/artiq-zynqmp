import sys,os,json,re,shutil,hashlib,time
from pathlib import Path
sys.path.insert(0,'/home/codex-hil/artiq-zynqmp/work/artiq-new-wip/scripts')
from test_candidate_runtime_hw import lease,preflight,bounded,REPO,CABLE
out=Path(__file__).resolve().parent
m=json.loads((REPO/'evidence/trained-observer-integration-2026-10-22/runtime-inputs.json').read_text())
result={'status':'FAIL','hardware_executed':False}
with lease() as held:
 started=time.monotonic()
 try:
  src=Path('/srv/codex-hil-data/artiq-zynqmp/build/abi-suite');dst=Path('/home/codex-hil/.local/state/artiq-builds/abi-suite-preserved-20261023')
  assert src.is_dir() and not src.is_symlink() and not dst.exists()
  shutil.copytree(src,dst,symlinks=True);count=0;total=0
  for p in src.rglob('*'):
   q=dst/p.relative_to(src)
   if p.is_symlink():assert q.is_symlink() and os.readlink(p)==os.readlink(q)
   elif p.is_file():
    assert hashlib.file_digest(p.open('rb'),'sha256').digest()==hashlib.file_digest(q.open('rb'),'sha256').digest()
    count+=1;total+=p.stat().st_size
  shutil.rmtree(src);src.symlink_to(dst,target_is_directory=True)
  (out/'relocation.json').write_text(json.dumps({'source':str(src),'destination':str(dst),'verified_files':count,'bytes':total,'method':'SHA256 verified copy then preserved path symlink'},indent=2)+'\n')
  files=preflight(m);env=os.environ.copy();env.pop('PYTHONPATH',None);env['GENESYS_LEASE_FD']=str(held.fileno())
  def run(name,args,timeout):
   print(name+' START',flush=True);code,text=bounded(args,timeout,env,held.fileno());(out/(name+'.log')).write_text(text)
   if code:raise RuntimeError(name+' failed')
   print(name+' PASS',flush=True)
  path=lambda n:files['restore_'+n]['path']
  result['hardware_executed']=True
  run('restore-load',[sys.executable,str(REPO/'scripts/load_rtio_runtime.py'),'--server','172.17.0.3:3121','--cable',CABLE,'--port','/dev/serial/by-id/usb-Digilent_Digilent_Adept_USB_Device_210383B7F02D-if01-port0','--ps-export',str(Path(path('fsbl')).parents[2]),'--bitstream',path('pl'),'--worker',str(Path(path('worker')).parent),'--cpu0',path('cpu0'),'--output',str(out/'load')],240)
  ip=json.loads((out/'load/results.json').read_text())['ip'];db=out/'device-db.py'
  text=(REPO/'examples/device_db_genesys.py').read_text();text,n=re.subn(r'([\"\']host[\"\']\s*:\s*[\"\'])\d+\.\d+\.\d+\.\d+([\"\'])',lambda match:match[1]+ip+match[2],text);assert n==1;db.write_text(text)
  run('restore-debug',['/srv/codex-hil-data/artiq-zynqmp/venvs/artiq-host/bin/python',str(REPO/'scripts/test_rtio_debug_hw.py'),'--ip',ip,'--device-db',str(db),'--artiq-run','/home/codex-hil/.local/bin/artiq_run','--output',str(out/'debug')],240)
  run('restore-ethernet',[sys.executable,str(REPO/'scripts/test_ethernet_hw.py'),'--ip',ip,'--interface','enp2s0','--output',str(out/'ethernet.json')],60)
  result.update(status='RESTORATION_PASS_AFTER_STORAGE_FAILURE',restored_ip=ip)
 except Exception as e:result['error']=str(e);raise
 finally:
  result['lease_seconds']=round(time.monotonic()-started,3);(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
