# SPDX-License-Identifier: LGPL-3.0-or-later
"""Explicit single status-only physical window; fixed register, no RAM or writes."""
import argparse,hashlib,json,os,re,secrets,socket,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'diagnostics/ddr'))
from test_candidate_runtime_hw import lease,bounded
from pit_sleep_observation import decode,ADDRESS
NAMES=['scripts/probe_pmu_sleep_status.tcl','scripts/test_candidate_runtime_hw.py','scripts/test_ethernet_hw.py','diagnostics/ddr/pit_sleep_observation.py']
def pins():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in NAMES}
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');a=p.parse_args()
 out=Path(__file__).resolve().parent
 if not a.execute:
  (out/'plan.json').write_text(json.dumps({'source_sha256':pins(),'address':hex(ADDRESS),'reads':1,'writes':False,'cable':'210383B7F02DA','ip':'192.168.2.3','mac':'02:38:3b:7f:02:0d'},indent=2)+'\n');print('PLAN_ONLY');return
 assert socket.gethostname()=='greg-OptiPlex-3070'
 plan=json.loads((out/'plan.json').read_text());assert plan['source_sha256']==pins()
 if (out/'result.json').exists():raise ValueError('refuse repeated window')
 nonce=secrets.randbits(64) or 1;env=os.environ.copy();cli='/home/codex-hil/.local/bin/hil-plug'
 private=Path('/home/codex-hil/.local/state/artiq-builds/pmu-status-plug-private-20261030.json')
 report={'hardware_executed':False,'deployable':False,'pmu_ram_access_allowed':False,'status':'FAIL','writes':False,'reads_requested':1,'nonce':nonce}
 with lease() as lock:
  z=subprocess.run([cli,'reserve','--owner','artiq-genesys: one RO sleep-status 20261030'],capture_output=True,text=True,timeout=25)
  if z.returncode:raise RuntimeError(z.stderr or z.stdout)
  held=json.loads(z.stdout);env['HIL_PLUG_TOKEN']=held['token']
  fd=os.open(private,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'w') as f:json.dump(held,f)
  try:
   def run(name,args,timeout):
    code,text=bounded(args,timeout,env,lock.fileno());(out/(name+'.log')).write_text(text)
    if code:raise RuntimeError(name+' failed; no retry')
    return text
   assert pins()==plan['source_sha256'];report['hardware_executed']=True
   for stage in ['before','after']:
    if stage=='after':
     cmd=['/home/codex-hil/.local/bin/vivado-container','shell','-c','exec "$@"','bash','/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',str(ROOT/'scripts/probe_pmu_sleep_status.tcl'),'tcp:172.17.0.3:3121','210383B7F02DA',str(nonce&0xffffffff),str(nonce>>32)]
     text=run('capture',cmd,35);matches=re.findall(r'^PMU_SLEEP_STATUS ([0-9a-f]{8}) ([0-9a-f]{8}) ([0-9a-f]{8})$',text,re.M)
     if len(matches)!=1:raise ValueError('one exact status marker required')
     hi,lo,value=map(lambda s:int(s,16),matches[0]);assert (hi<<32|lo)==nonce
     record=dict(version=1,nonce=nonce,address=ADDRESS,return_code=0,value=value)
     report['record']=record;report['interpretation']=decode(record,nonce)
    run(stage+'-ethernet',[sys.executable,str(ROOT/'scripts/test_ethernet_hw.py'),'--ip','192.168.2.3','--interface','enp2s0','--output',str(out/(stage+'-ethernet.json'))],30)
    result=json.loads((out/(stage+'-ethernet.json')).read_text());assert result['mac']==plan['mac'] and all(v=='PASS' for v in result['tests'].values())
   report['status']='SINGLE_STATUS_AND_BEFORE_AFTER_ETHERNET_PASS';report['source_pins_unchanged']=pins()==plan['source_sha256']
  except Exception as ex:report['error']=str(ex)
  finally:
   z=subprocess.run([cli,'release'],env=env,capture_output=True,text=True,timeout=25)
   report['plug_released']=z.returncode==0
   if z.returncode==0:private.unlink()
   (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
