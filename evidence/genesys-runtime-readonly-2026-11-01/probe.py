# SPDX-License-Identifier: LGPL-3.0-or-later
"""Bounded normal runtime log read; no reset/config/experiment commands."""
import datetime,fcntl,json,os,socket,subprocess,time
from pathlib import Path
OUT=Path(__file__).resolve().parent
CLI='/home/codex-hil/.local/bin/hil-plug'
def call(args,env=None,timeout=20):
 z=subprocess.run(args,capture_output=True,text=True,timeout=timeout,env=env)
 return dict(returncode=z.returncode,stdout=z.stdout,stderr=z.stderr)
def main():
 assert socket.gethostname()=='greg-OptiPlex-3070' and os.getuid()==1001
 private=Path('/home/codex-hil/.local/state/artiq-builds/genesys-runtime-readonly-20261101');private.mkdir(mode=0o700,exist_ok=False)
 r=dict(start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reset=False,power_switch=False,register_memory_access=False,experiment_run=False);env=None;start=time.monotonic()
 with open('/home/codex-hil/.cache/genesys-210383B7F02DA.lock','a') as lock:
  try:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r['board_lock']=True
   z=call([CLI,'reservation']);assert z['returncode']==0;assert not json.loads(z['stdout']).get('lease'),'Plug busy'
   z=call([CLI,'reserve','--owner','genesys-native-runtime-readonly-20261101']);assert z['returncode']==0
   token=json.loads(z['stdout'])['token'];env=dict(os.environ,HIL_PLUG_TOKEN=token)
   fd=os.open(private/'token',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
   with os.fdopen(fd,'w') as f:f.write(token)
   r['route']=call(['ip','route','get','192.168.2.3']);assert 'dev enp2s0' in r['route']['stdout'],'Route changed'
   r['icmp']=call(['ping','-n','-I','enp2s0','-c','1','-W','2','192.168.2.3'],timeout=5)
   assert r['icmp']['returncode']==0,'Single ICMP failed; no service probe'
   r['neighbor']=call(['ip','neigh','show','192.168.2.3','dev','enp2s0'])
   words=r['neighbor']['stdout'].lower().split();assert '02:38:3b:7f:02:0d' in words,'MAC mismatch'
   assert 'reachable' in words,'Neighbor not freshly REACHABLE; no application probe'
   r['management_log']=call(['/home/codex-hil/.local/bin/artiq_coremgmt','-D','192.168.2.3','log'],timeout=12)
   assert r['management_log']['returncode']==0,'Management log failed; no retry'
   r['status']='NORMAL_MANAGEMENT_LOG_READ_PASS'
  except Exception as e:r.update(status='PROBE_STOP_NO_RETRY',error=str(e))
  finally:
   if env:
    r['release']=call([CLI,'release'],env)
    if r['release']['returncode']==0:(private/'token').unlink()
   r['elapsed_seconds']=round(time.monotonic()-start,3)
   (OUT/'report.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2))
if __name__=='__main__':main()
