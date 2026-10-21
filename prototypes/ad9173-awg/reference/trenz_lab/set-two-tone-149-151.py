"""Set main DAC NCOs to 149/151 MHz, preserve FPGA JESD payload 0x7FFF.
Volatile SPI only. Scope then Trenz locks; rollback frequencies on failure.
"""
import json,fcntl,datetime
from pathlib import Path
from jtag_spi import Session,ROOT
from rf_measure import Scope
FS=4915200000
report={'hardware':True,'status':'IN_PROGRESS','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'dac_sample_rate_hz':FS,'lane_rate_bps':6144000000,'fpga_payload_i':32767,'fpga_payload_q':0,'tones_hz':{'DAC0':149000000,'DAC1':151000000},'stages':[]}
saved={};changed=False
with (Path.home()/'.cache/mso4104-C020817.lock').open('a+') as lease:
 fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with Session() as s:
  def run(ops,label):
   x=s.run(ops,'two-tone-'+label);report['stages'].append({'label':label,**x});return x
  def read(keys,label):return {r['address']:r['value'] for r in run([('r',a) for a in keys],label)['operations']}
  try:
   g=read([4,5,8,0x300,0x110,0x111,0x799,0x7b5],'identity-clock')
   assert (g[4],g[5])==(0x73,0x91) and g[0x7b5]&1 and g[0x799]&63==5 and g[0x110]==0x23 and g[0x111]==0x82
   for page in [0x40,0x80]:
    run([('w',8,page)],f'save-page-{page}');saved[page]=read([0x112,0x113,0x1e6,0x596]+list(range(0x114,0x11a)),f'save-{page}')
    assert saved[page][0x112]==8 and saved[page][0x1e6]==0 and saved[page][0x596]==12
   report['before']={str(p):{hex(a):v for a,v in vals.items()} for p,vals in saved.items()}
   changed=True;run([('f',0),('wait',10)],'mute-payload')
   report['ftw']={}
   for dac,page,freq in [(0,0x40,149000000),(1,0x80,151000000)]:
    ftw=(freq*(1<<48)+FS//2)//FS
    ops=[('w',8,page),('w',0x113,0)]+[('w',0x114+i,(ftw>>(8*i))&255) for i in range(6)]+[('w',0x113,1),('wait',10)]
    run(ops,f'program-dac{dac}');vals=read([0x113]+list(range(0x114,0x11a)),f'verify-dac{dac}')
    assert vals[0x113]&2 and sum(vals[0x114+i]<<(8*i) for i in range(6))==ftw
    report['ftw'][str(dac)]={'word':hex(ftw),'actual_nominal_hz':ftw*FS/(1<<48)}
   run([('w',8,0xc0),('f',32767),('wait',200)],'enable')
   with Scope() as scope:
    scope.io.write('CH1:SCA .2');scope.io.write('CH2:SCA .2')
    report['rf']=scope.capture('149-151-MHz',targets=[(1,151000000),(2,149000000)])
    for c in report['rf']['channels'].values():assert c['tone_detected'] and abs(c['fit_hz']-c['expected_hz'])<100000,'RF tone verification failed'
   report['links']=[]
   for link in [0,1]:
    run([('w',0x300,11|(link<<2))],f'link-page-{link}')
    vals=read([0x470,0x471,0x472,0x473,0x46d,0x46e,0x46f,0x490,0x491],f'link-{link}');report['links'].append({hex(a):v for a,v in vals.items()})
    assert all(vals[a]&3==3 for a in [0x470,0x471,0x472,0x473]) and all(vals[a]&3==0 for a in [0x46d,0x46e,0x46f]) and all(vals[a]&7==0 for a in [0x490,0x491])
   run([('w',8,g[8]),('w',0x300,g[0x300])],'restore-page-selectors')
   report['status']='PASS_TWO_TONES_149_151_MHZ_JESD';report['final_state']='RUNNING_TONES_149_151_MHZ_FULL_POSITIVE_FPGA_I_SCALE'
  except Exception as e:
   report['status']='FAIL';report['error']=str(e)
   if changed:
    try:
     ops=[('f',0)]
     for page,vals in saved.items():ops += [('w',8,page),('w',0x113,0)]+[('w',a,vals[a]) for a in range(0x114,0x11a)]+[('w',0x113,1),('wait',10)]
     run(ops+[('f',32767),('w',8,g[8]),('w',0x300,g[0x300])],'rollback');report['rollback']='PASS_PREVIOUS_FREQUENCIES'
    except Exception as e:report['rollback_error']=str(e)
  finally:
   report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(ROOT/'two-tone-149-151-2026-10-21.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['stages','rf']},indent=2))
if not report['status'].startswith('PASS'):raise SystemExit(2)
