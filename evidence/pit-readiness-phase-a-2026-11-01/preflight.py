# SPDX-License-Identifier: LGPL-3.0-or-later
"""Bounded read-only readiness. No power/reset/programming/PMU memory commands."""
import datetime,fcntl,hashlib,json,os,socket,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
PRIVATE=Path('/home/codex-hil/.local/state/artiq-builds/pit-readiness-phase-a-20261101-v1')
CLI='/home/codex-hil/.local/bin/hil-plug'
LOCK=Path('/home/codex-hil/.cache/genesys-210383B7F02DA.lock')
OWNER='genesys-native-phase-a-20261101-readonly'
def call(args,env=None,timeout=30):
 z=subprocess.run(args,capture_output=True,text=True,timeout=timeout,env=env)
 return dict(returncode=z.returncode,stdout=z.stdout,stderr=z.stderr)
def main():
 if socket.gethostname()!='greg-OptiPlex-3070' or os.getuid()!=1001:raise ValueError('owning station identity mismatch')
 PRIVATE.mkdir(mode=0o700,exist_ok=False)
 r=dict(start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),hostname=socket.gethostname(),uid=os.getuid(),device_access=False,power_switched=False,reset=False,programmed=False,pmu_memory_access=False,gpo_access=False,network_probe_executed=False,board_lock=False,plug_reserved=False,plug_released=False,owner=OWNER)
 tokenfile=PRIVATE/'token.json';env=None;start=time.monotonic()
 fd=os.open(LOCK,os.O_RDWR|os.O_CREAT,0o600)
 try:
  try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:r['status']='BOARD_BUSY_NO_DEVICE_ACCESS';return
  r['board_lock']=True
  r['reservation_before']=call([CLI,'reservation'])
  if r['reservation_before']['returncode']:r['status']='PLUG_RESERVATION_METADATA_UNAVAILABLE';return
  public=json.loads(r['reservation_before']['stdout'])
  if public.get('lease'):r['status']='PLUG_BUSY_NO_DEVICE_ACCESS';return
  reserved=call([CLI,'reserve','--owner',OWNER])
  if reserved['returncode']:r['status']='PLUG_RESERVE_FAILED';r['reserve_error']=reserved['stderr'];return
  lease=json.loads(reserved['stdout']);token=lease['token']
  fdtoken=os.open(tokenfile,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fdtoken,'w') as f:json.dump(lease,f)
  r['plug_reserved']=True;env=dict(os.environ,HIL_PLUG_TOKEN=token)
  r['plug_status']=call([CLI,'status'],env=env);r['device_access']=True
  serial=Path('/dev/serial/by-id/usb-Digilent_Digilent_Adept_USB_Device_210383B7F02D-if01-port0')
  r['uart_metadata']=dict(stable_path=str(serial),exists=serial.exists(),resolved=str(serial.resolve()) if serial.exists() else None,opened=False)
  if serial.exists():r['udev']=call(['udevadm','info','--query=property','--name',str(serial)])
  r['neighbor_cache']=call(['ip','neigh','show','192.168.2.3'])
  r['network_not_run_reason']='Passive neighbor cache/old IP is not independent current board-runtime identity'
  r['disk_free_bytes']={str(p):os.statvfs(p).f_bavail*os.statvfs(p).f_frsize for p in [Path('/'),Path('/srv/codex-hil-data')]}
  manifest=json.loads((ROOT/'evidence/trained-observer-integration-2026-10-22/runtime-inputs.json').read_text());pins={}
  for n,item in manifest['files'].items():
   if n.startswith('restore_') or n in ['candidate_pmu','candidate_fsbl']:
    p=Path(item['path']);pins[n]=dict(path=str(p),exists=p.exists(),sha256_matches=hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'] if p.exists() else False)
  r['baseline_file_checks']=pins
  r['status']='READ_ONLY_PHASE_A_COMPLETED_NOT_ENTRY_ADMISSION'
 except Exception as exc:r['status']='PREFLIGHT_ERROR_NO_MUTATION_RECOVERY';r['error']=type(exc).__name__+': '+str(exc)
 finally:
  if r['plug_reserved'] and env:
   try:
    release=call([CLI,'release'],env=env);r['release_result']=release;r['plug_released']=release['returncode']==0
    if r['plug_released']:tokenfile.unlink()
   except Exception as exc:r['release_error']=type(exc).__name__+': '+str(exc)
  r['elapsed_seconds']=round(time.monotonic()-start,3)
  if r['board_lock']:fcntl.flock(fd,fcntl.LOCK_UN)
  os.close(fd);r['board_lock_released']=bool(r['board_lock']);r['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  (HERE/'report.json').write_text(json.dumps(r,indent=2)+'\n')
  print(json.dumps({k:r[k] for k in ['status','device_access','power_switched','board_lock','plug_reserved','plug_released','elapsed_seconds']}))
if __name__=='__main__':main()
