#!/usr/bin/env python3
"""One normal-PMU restoration qualification, offline by default. LGPL-3.0-or-later."""
import argparse,hashlib,json,os,re,sys,time
from pathlib import Path
from test_candidate_runtime_hw import REPO,CABLE,preflight,lease,bounded,verify_pmu_restore_stages
from check_hw_storage import RestoreReserve,runtime_paths,require_runtime_space
SCRIPTS={
 'scripts/qualify_pmu_restore_hw.py','scripts/test_candidate_runtime_hw.py',
 'scripts/check_remote_rtio_build.py','scripts/check_hw_storage.py',
 'scripts/restart_pmu_for_restore.tcl','scripts/load_rtio_runtime.py',
 'scripts/reset_genesys_ps.tcl','scripts/run_boot_firmware.tcl',
 'scripts/program_genesys_pl.tcl','scripts/prepare_local_rtio.tcl',
 'scripts/run_kernel_worker.tcl','scripts/run_a53_runtime.tcl',
 'scripts/test_rtio_debug_hw.py','scripts/test_ethernet_hw.py',
 'examples/device_db_genesys.py'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def plan(runtime):
 preflight(json.loads(runtime.read_text()))
 return dict(kind='NORMAL_PMU_RECOVERY_QUALIFICATION_V1',runtime={'path':str(runtime.resolve()),'sha256':sha(runtime)},script_sha256={n:sha(REPO/n) for n in sorted(SCRIPTS)},guard=False,aib_writes=False,retries=0)
def validate(m):
 if set(m)!={'kind','runtime','script_sha256','guard','aib_writes','retries'} or m['kind']!='NORMAL_PMU_RECOVERY_QUALIFICATION_V1' or m['guard'] is not False or m['aib_writes'] is not False or type(m['retries']) is not int or m['retries']!=0:raise ValueError('Wrong recovery scope')
 if set(m['script_sha256'])!=SCRIPTS:raise ValueError('Incomplete recovery pins')
 for n,h in m['script_sha256'].items():
  if sha(REPO/n)!=h:raise ValueError('Changed recovery helper '+n)
 if sha(m['runtime']['path'])!=m['runtime']['sha256']:raise ValueError('Changed runtime manifest')
 return preflight(json.loads(Path(m['runtime']['path']).read_text()))
def bootstrap(run,command):
 text=run('pmu-bootstrap',command,60)
 verify_pmu_restore_stages(text)
 return True

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--runtime',type=Path,default=REPO/'evidence/trained-observer-integration-2026-10-22/runtime-inputs.json')
 p.add_argument('--manifest',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--execute',action='store_true')
 for k in ('server','port','interface'):p.add_argument('--'+k)
 a=p.parse_args()
 if a.execute and (not a.manifest or not all((a.server,a.port,a.interface))):p.error('Execution requires fresh manifest/server/port/interface')
 m=json.loads(a.manifest.read_text()) if a.manifest else plan(a.runtime);files=validate(m)
 out=a.output.resolve()
 if out.exists():raise ValueError('Fresh output required')
 out.mkdir(parents=True);(out/'inputs.json').write_text(json.dumps(m,indent=2)+'\n')
 if not a.execute:
  (out/'results.json').write_text(json.dumps({'status':'PREFLIGHT_PASS_NO_HARDWARE','hardware_executed':False},indent=2)+'\n');print('PREFLIGHT_PASS_NO_HARDWARE');return 0
 result={'status':'FAIL','hardware_executed':False,'scope':'normal PMU bootstrap then normal runtime only','stages':{}};start=time.monotonic()
 try:
  with lease() as fd:
   validate(m);require_runtime_space(out,REPO)
   with RestoreReserve(runtime_paths(out,REPO)) as reserve:
    env=os.environ.copy();env.pop('PYTHONPATH',None);env['GENESYS_LEASE_FD']=str(fd.fileno())
    def run(name,command,timeout):
     print(name+' START',flush=True)
     try:code,text=bounded(command,timeout,env,fd.fileno())
     except BaseException as e:
      (out/(name+'.log')).write_text((getattr(e,'output','') or '')+str(e));raise
     (out/(name+'.log')).write_text(text);result['stages'][name]=code
     if code:raise RuntimeError(name+' failed; no retry')
     print(name+' PASS',flush=True);return text
    result['hardware_executed']=True
    bootstrap(run,['vivado-container','shell','-c','exec "$@"','bash',
     '/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',str(REPO/'scripts/restart_pmu_for_restore.tcl'),a.server,files['restore_pmu']['path'],CABLE])
    reserve.release();result['reserve_released_before_normal_load']=True
    ps=Path(files['restore_fsbl']['path']).parents[2];worker=Path(files['restore_worker']['path']).parent
    run('load',[sys.executable,str(REPO/'scripts/load_rtio_runtime.py'),'--server',a.server,'--cable',CABLE,'--port',a.port,'--ps-export',str(ps),'--bitstream',files['restore_pl']['path'],'--worker',str(worker),'--cpu0',files['restore_cpu0']['path'],'--output',str(out/'load')],240)
    loaded=json.loads((out/'load/results.json').read_text())
    if loaded['status']!='PASS':raise ValueError('Normal load incomplete')
    ip=loaded['ip'];result['ip']=ip;db=out/'device-db.py'
    text,n=re.subn(r'([\"\']host[\"\']\s*:\s*[\"\'])\d+\.\d+\.\d+\.\d+([\"\'])',lambda x:x[1]+ip+x[2],(REPO/'examples/device_db_genesys.py').read_text())
    if n!=1:raise ValueError('Unexpected database address')
    db.write_text(text)
    run('debug',['/srv/codex-hil-data/artiq-zynqmp/venvs/artiq-host/bin/python',str(REPO/'scripts/test_rtio_debug_hw.py'),'--ip',ip,'--device-db',str(db),'--artiq-run',str(Path.home()/'.local/bin/artiq_run'),'--output',str(out/'debug')],240)
    run('ethernet',[sys.executable,str(REPO/'scripts/test_ethernet_hw.py'),'--ip',ip,'--interface',a.interface,'--output',str(out/'ethernet.json')],90)
    result['status']='PASS';result['normal_runtime_verified']=True
 except Exception as e:result['error']=str(e);result['normal_runtime_verified']=False
 finally:
  result['elapsed_seconds']=round(time.monotonic()-start,3);(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
