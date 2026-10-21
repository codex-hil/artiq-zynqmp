"""Bounded live FPGA/JESD/RF validation; no programming or clock changes.
Requires payload-fixed diagnostic bitstream already running. Locks scope then Trenz.
"""
import json,fcntl,hashlib,datetime
from pathlib import Path
from jtag_spi import Session,ROOT
from rf_measure import Scope
report={'hardware':True,'status':'IN_PROGRESS','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'lane_rate_bps':6144000000,'dac_sample_rate_hz':4915200000,'stages':[],'programming':'NONE_LIVE_VALIDATION','bitstream':'fabric_spi_slow6144.bit','bitstream_sha256':hashlib.sha256((ROOT/'fabric_spi_slow6144.bit').read_bytes()).hexdigest()}
with (Path.home()/'.cache/mso4104-C020817.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with Session() as s:
  def run(ops,label):
   result=s.run(ops,'live-'+label);report['stages'].append({'label':label,**result});return result
  def read(addrs,label):return {hex(r['address']):r['value'] for r in run([('r',a) for a in addrs],label)['operations']}
  try:
   report['global']=read([4,5,0x7b5,0x799,0x110,0x111,0x100,0x90,0x200,0x201,0x300],'global')
   g=report['global'];assert g['0x4']==0x73 and g['0x5']==0x91 and g['0x7b5']&1
   assert g['0x799']&63==5 and g['0x110']==0x23 and g['0x111']==0x82 and g['0x100']==0 and g['0x90']==0 and g['0x200']==0
   run([('w',0xc7,0),('w',0xc7,1),('diag',),('wait',500),('diag',)],'clock-check')
   assert read([0xc3],'dll')['0xc3']&1
   a,b=report['stages'][-2]['diagnostics'];report['tx_to_reference_clock_ratio']=((b['jesd_count']-a['jesd_count'])&0xffffffff)/((b['ref_count']-a['ref_count'])&0xffffffff)
   assert abs(report['tx_to_reference_clock_ratio']-.625)<.001
   report['dsp']={}
   for page in [1,8,0x40,0x80]:
    run([('w',8,page)],f'page-{page}')
    keys=[0x130,0x131,0x146,0x147] if page<64 else [0x112,0x113,0x1e6,0x596]+list(range(0x114,0x11a))
    vals=read(keys,f'dsp-{page}');report['dsp'][str(page)]=vals
    if page<64:assert vals['0x130']==0x40 and vals['0x131']&2 and vals['0x146']==0 and vals['0x147']==8
    else:assert vals['0x1e6']==0 and vals['0x112']==8 and vals['0x596']==12
   run([('w',8,0xc0)],'main-page')
   report['rf_cases']=[]
   with Scope() as scope:
    for name,code in [('high',0x2020),('half',0x1010),('zero',0),('recovered',0x2020),('asymmetric',0x5a82),('fullscale',0x7fff)]:
     scale='.05' if code<=0x2020 else '.2'
     scope.io.write('CH1:SCA '+scale);scope.io.write('CH2:SCA '+scale)
     run([('f',code),('wait',200)],name)
     case=scope.capture(name,targets=[(1,76800000),(2,38400000)]);case['payload_word']=code;report['rf_cases'].append(case)
    for ch in ['1','2']:
     hi,half,zero,recovered,asym,full=[c['channels'][ch] for c in report['rf_cases']]
     assert all(c['tone_detected'] for c in [hi,half,recovered,asym,full]),'Tone missing'
     assert .4<half['fit_vpp']/hi['fit_vpp']<.6,'Half amplitude mismatch'
     assert zero['fit_vpp']<hi['fit_vpp']*.15,'Zero failed to mute'
     assert .85<recovered['fit_vpp']/hi['fit_vpp']<1.15,'Recovery mismatch'
     for code,case in [(0x5a82,asym),(0x7fff,full)]:assert .85<case['fit_vpp']/(hi['fit_vpp']*code/0x2020)<1.15,'Asymmetric word scaling/byte order mismatch'
   report['link_samples']=[]
   for sample in range(3):
    pair=[]
    for link in [0,1]:
     run([('w',0x300,11|(link<<2))],f'link-page-{sample}-{link}')
     vals=read([0x470,0x471,0x472,0x473,0x46c,0x46d,0x46e,0x46f,0x400,0x40a,0x40d,0x40e,0x415,0x416,0x490,0x491],f'link-{sample}-{link}')
     assert all(vals[hex(a)]&3==3 for a in [0x470,0x471,0x472,0x473]) and vals['0x400']==0x61
     assert all(vals[hex(a)]&3==0 for a in [0x46d,0x46e,0x46f]) and all(vals[hex(a)]&7==0 for a in [0x490,0x491])
     pair.append(vals)
    report['link_samples'].append(pair)
   run([('w',0x300,g['0x300']),('diag',)],'final')
   report['status']='PASS_DUAL_JESD_FPGA_PAYLOAD_RF_SCALING_ZERO_RECOVERY_FULLSCALE';report['final_payload_word']=0x7fff;report['final_state']='RUNNING_VOLATILE_FPGA_JESD_MAIN_NCO_UPCONVERSION_INTERNAL_DC_DISABLED'
  except Exception as e:
   report['status']='FAIL';report['error']=str(e)
   try:run([('f',0x5a82),('w',8,0xc0)],'restore-known-payload');report['final_payload_word']=0x5a82
   except Exception as e:report['restore_error']=str(e)
  finally:
   report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(ROOT/'payload-rf-pass-2026-10-21.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['stages','rf_cases','link_samples']},indent=2))
if not report['status'].startswith('PASS'):raise SystemExit(2)
