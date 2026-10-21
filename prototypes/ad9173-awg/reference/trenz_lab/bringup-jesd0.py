"""Bounded AD9173 dual-link mode3 Subclass0 test; restore NCO baseline.
SPI via FPGA USER2 only, USB disconnected. No SD/flash/OTP writes.
"""
import json,time,sys,fcntl,hashlib
from pathlib import Path
from jtag_spi import Session,ROOT
report={'hardware':True,'status':'IN_PROGRESS','mode':3,'dual_link':True,'subclass':0,'hd':0,'lane_rate_bps':7372800000,'stages':[]};snapshot={};pages={};qbd={};changed=False;loaded=False;leave_running=False
combined='--prbs-then-rf' in sys.argv
slow='--slow-6144' in sys.argv
all_phys='--all-phys' in sys.argv
native_prbs='--native-prbs7' in sys.argv
prbs='--phy-prbs7' in sys.argv or native_prbs
sync_force='--sync-force-test' in sys.argv
native_hd1='--native-hd1' in sys.argv
native_8b10b='--native-8b10b' in sys.argv or native_hd1 or slow
report['hd']=1 if native_hd1 else 0
rf='--rf' in sys.argv
diagnostic_rf='--diagnostic-rf' in sys.argv
report['fpga_codec']='GTHE4_NATIVE_8B10B' if native_8b10b else 'LITEX_SOFTWARE_8B10B'
report['phy_prbs7']=prbs
report['native_prbs7']=native_prbs
report['all_phys']=all_phys
report['slow_6144']=slow
report['combined']=combined
if slow:report.update(hd=1,lane_rate_bps=6144000000,dac_sample_rate_hz=4915200000,expected_did=0x61)
rf_lock=None
if rf:
 rf_lock=(Path.home()/'.cache/mso4104-C020817.lock').open('a+');fcntl.flock(rf_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
with Session() as s:
 def run(ops,label):
  result=s.run(ops,label);report['stages'].append({'label':label,**result});return result
 def read(keys,label):return {row['address']:row['value'] for row in run([('r',a) for a in keys],label)['operations']}
 def writes(pairs):return [('w',a,v) for a,v in pairs]
 try:
  report['zero_payload_bit']='--zero-payload-bit' in sys.argv
  selected_bit=ROOT/('fabric_spi_slow6144-zero-payload-bug.bit' if '--zero-payload-bit' in sys.argv else 'fabric_spi_slow6144.bit' if slow else 'fabric_spi_native_prbs7.bit' if native_prbs else 'fabric_spi_prbs7.bit' if prbs else 'fabric_spi_native_hd1.bit' if native_hd1 else 'fabric_spi_native_8b10b.bit' if native_8b10b else 'fabric_spi_jesd0_stream.bit')
  report['bitstream']=str(selected_bit)
  report['bitstream_sha256']=hashlib.sha256(selected_bit.read_bytes()).hexdigest()
  s.program(selected_bit,'jesd0-program');loaded=True
  run([('w',0,0x18)],'jesd0-spi-init')
  ids=read([4,5,0x7b5],'jesd0-identity');assert [ids[a] for a in [4,5]]==[0x73,0x91];assert ids[0x7b5]&1
  global_keys=[8,0x3f,0x1de,0x90,0x100,0x110,0x111,0x200,0x201,0x203,0x210,0x212,0x213,0x216,0x253,0x254,0x280,0x300,0x308,0x309,0x30a,0x30b,0x334,0x32c,0x32d,0x32e,0x32f,0x084,0x03a,0x03b,0x312]+list(range(0x240,0x24c))+list(range(0x315,0x31a))+[0x31e]+([0x799,0x792,0xc0,0xc1,0xc7,0xdb] if slow else [])
  report['mute_method']='TXEN_DIGITAL_DAC_BIAS_ON'
  snapshot=read(global_keys,'jesd0-global-before');report['snapshot']={hex(a):v for a,v in snapshot.items()}
  changed=True
  run([('w',0x90,0),('w',0x1de,3),('w',0x300,snapshot[0x300]&~3)],'jesd0-disable-links-keep-bias')
  for page in [0x41,0x82,1,8]+([2,4,16,32] if '--dsp-debug' in sys.argv else []):
   run([('w',8,page)],'jesd0-select-page-'+str(page));pages[page]=read([0x1e6,0x130,0x131,0x146,0x147,0x148,0x149,0x596]+list(range(0x132,0x138)),'jesd0-page-before-'+str(page))
  for link in [0,1]:
   run([('w',0x300,8|(link<<2))],'jesd0-select-link-'+str(link));qbd[link]=read(list(range(0x450,0x45a))+[0x45b,0x45c,0x45d,0x475,0x476,0x480,0x481],'jesd0-qbd-before-'+str(link))
  run([('w',8,0xc0),('w',0x596,4),('w',0x3f,0x30),('w',0x90,0)],'jesd0-digital-mute-keep-bias')
  if slow:
   run([('w',0x100,1),('w',0x799,(snapshot[0x799]&0xc0)|5),('w',0x792,snapshot[0x792]|2),('w',0x792,snapshot[0x792]&~2),('wait',150),('w',0xc0,0),('w',0xdb,0),('w',0xdb,1),('w',0xdb,0),('w',0xc1,0x68),('w',0xc1,0x69),('w',0xc7,1),('wait',100)],'slow-dac-pll-dll')
   clock=read([0x799,0x7b5,0xc3],'slow-dac-clock-status');assert clock[0x7b5]&1 and clock[0xc3]&1,'Slow DAC PLL/DLL did not lock'
  # Same HMC source as the DAC; only output13 and divider restart/reseed requests.
  hw=[(0x14a,0),(0x14b,12 if slow else 16),(0x14c,0),(0x151,0),(0x152,0x10),(0x14a,0xd1),(1,0x42)]
  run([('h',a,v) for a,v in hw]+[('wait',10),('h',1,0x40),('h',1,0xc0),('wait',1),('h',1,0x40),('wait',250),('diag',)],'jesd0-fpga-clock')
  diag=report['stages'][-1]['diagnostics'][-1];assert diag['flags']&31==31,'FPGA QPLL/TX not ready'
  run(writes([(0x100,0),(0x300,8),(0x110,0x23),(0x111,0x82),(0x084,1),(0x312,0x10)]),'jesd0-mode')
  cfg=read([0x110,0x111,0x300],'jesd0-mode-readback');assert not cfg[0x110]&128,'Invalid mode'
  if slow:
   run([('w',8,0xc0),('w',0x113,0),('w',0x113,1),('wait',10)],'slow-reload-main-ncos')
   if rf:
    from rf_measure import Scope
    run([('w',0x3f,0),('w',0x596,12),('wait',200)],'slow-internal-nco-preview-enable')
    with Scope() as scope:
     scope.io.write('CH1:SCA .1');scope.io.write('CH2:SCA .1')
     report['internal_nco_clock_preview']=scope.capture('internal-nco-clock-check',targets=[(1,76800000),(2,38400000)])
    run([('w',8,0xc0),('w',0x596,4),('w',0x3f,0x30)],'slow-internal-nco-preview-mute')
    assert all(ch['tone_detected'] for ch in report['internal_nco_clock_preview']['channels'].values()),'Internal NCO clock preview failed'

  for link in [0,1]:
   run(writes([(0x300,8|(link<<2)),(0x475,9),(0x450,0x61 if slow else 0),(0x451,link),(0x452,0),(0x453,0x81),(0x454,1),(0x455,31),(0x456,1),(0x457,15),(0x458,15),(0x459,0x20),(0x45b,0),(0x45c,0),(0x45d,(0xa4 if slow else 0x43 if native_hd1 else 0x42)+link),(0x476,0x14),(0x480,0x38),(0x481,0x38),(0x475,1)]),'jesd0-qbd-config-'+str(link))
   read(list(range(0x450,0x45b)),'jesd0-qbd-config-readback-'+str(link))
  eq=[(0x240,0xaa),(0x241,0xaa),(0x242,0x55),(0x243,0x55)]+[(a,0x1f) for a in range(0x244,0x24c)]
  serdes=[(0x201,0 if all_phys else 0x0f),(0x203,0),(0x253,1),(0x254,1),(0x210,0x16),(0x216,5),(0x212,255),(0x212,0),(0x210,0x87),(0x216,0x11),(0x213,1),(0x213,0),(0x200,0)]
  run(writes(eq+serdes)+[('wait',100)],'jesd0-serdes-start')
  seq=[(0x210,0x86),(0x216,0x40),(0x213,1),(0x213,0),(0x210,0x86),(0x216,0),(0x213,1),(0x213,0),(0x210,0x87),(0x216,1),(0x213,1),(0x213,0),(0x280,5),(0x280,1)]
  run(writes(seq)+[('wait',200)],'jesd0-serdes-pll')
  pll=read([0x281,0x7b5],'jesd0-pll-status');assert pll[0x281]&1,'DAC SERDES PLL not locked';assert pll[0x7b5]&1
  if native_prbs:
   if slow:run([('f',0x8000),('wait',10)],'slow-fpga-native-prbs-enable')
   run([('diag',),('wait',500),('diag',)],'native-prbs-clock-count')
   a=report['stages'][-1]['diagnostics'][0];b=report['stages'][-1]['diagnostics'][-1]
   report['tx_clock_to_ref_ratio']=((b['jesd_count']-a['jesd_count'])&0xffffffff)/((b['ref_count']-a['ref_count'])&0xffffffff)
  if sync_force:
   report['sync_force_cases']=[]
   run([('w',0x300,11),('w',0x475,5),('w',0x300,15),('w',0x475,5),('wait',100),('diag',)],'sync-force-both')
   report['sync_force_cases'].append({'name':'both_low','diag':report['stages'][-1]['diagnostics'][-1]})
   run([('w',0x300,11),('w',0x475,1),('wait',100),('diag',)],'sync-release-0')
   report['sync_force_cases'].append({'name':'release_0','diag':report['stages'][-1]['diagnostics'][-1]})
   run([('w',0x300,11),('w',0x475,5),('w',0x300,15),('w',0x475,1),('wait',100),('diag',)],'sync-release-1')
   report['sync_force_cases'].append({'name':'release_1','diag':report['stages'][-1]['diagnostics'][-1]})
   for case in report['sync_force_cases']:case['pin_levels']=(case['diag']['flags']>>7)&3
   report['status']='PASS_SYNC_FORCE' if [c['pin_levels'] for c in report['sync_force_cases']]==[0,1,2] else 'FAIL_SYNC_FORCE_OR_CGS'
  elif prbs:
   report['prbs_cases']=[]
   run(writes([(0x315,0xff if all_phys else 0xf0),(0x317,1),(0x318,0),(0x319,0)]),'prbs-enable')
   selected_inverse=0
   cases=[('prbs7',0,1000,0),('prbs7-inverted',0,1000,255),('wrong-prbs15',4,20,None),('prbs7-recovery',0,1000,None)] if native_prbs else [('prbs7',0,1000,0),('wrong-prbs15',4,20,0),('prbs7-recovery',0,1000,0)]
   for name,pattern,duration,inverse in cases:
    inverse=selected_inverse if inverse is None else inverse
    run([('w',0x334,inverse)],'prbs-polarity-'+name)
    run([('w',0x316,pattern|1),('wait',1),('w',0x316,pattern),('w',0x316,pattern|2),('w',0x316,pattern|3),('wait',1),('w',0x316,pattern|2),('w',0x317,1),('w',0x318,0),('w',0x319,0),('wait',duration)],'prbs-run-'+name)
    flags=read([0x315,0x31d,0x281],'prbs-flags-'+name)
    counts={};captures={}
    for phy in (range(8) if all_phys else range(4,8)):
     ops=[('w',0x316,(phy<<4)|pattern|2)]+[('r',a) for a in [0x31a,0x31b,0x31c]]
     if all_phys:ops += [('w',0x31e,0),('w',0x31e,1)]+[('r',a) for a in range(0x31f,0x324)]
     result=run(ops,f'prbs-count-{name}-{phy}')
     count={row['address']:row['value'] for row in result['operations'] if row['kind']=='r'}
     counts[str(phy)]=sum(count[0x31a+i]<<(8*i) for i in range(3))
     if all_phys:captures[str(phy)]=hex(sum(count[0x31f+i]<<(8*i) for i in range(5)))
    report['prbs_cases'].append({'name':name,'nominal_duration_ms':duration,'flags':{hex(a):v for a,v in flags.items()},'errors':counts,'inverse_mask':inverse,'raw40':captures})
    if name.startswith('prbs7') and sum(v==0 for v in counts.values())>=4:selected_inverse=inverse
   candidates=report['prbs_cases'][:2] if native_prbs else report['prbs_cases'][:1]
   first=max(candidates,key=lambda c:sum(v==0 for v in c['errors'].values()));negative,recovered=report['prbs_cases'][-2:]
   report['qualified_inverse_mask']=first['inverse_mask']
   qualified=[phy for phy,v in first['errors'].items() if v==0];report['qualified_physical_lanes']=qualified
   mask=sum(1<<int(phy) for phy in qualified)
   prbs_pass=len(qualified)>=4 and all(negative['errors'][phy]>0 and recovered['errors'][phy]==0 for phy in qualified) and first['flags']['0x31d']&mask==mask and recovered['flags']['0x31d']&mask==mask
   report['prbs_status']='PASS' if prbs_pass else 'FAIL'
   report['status']='PASS_FOUR_PHYSICAL_LANES_PRBS7_NEGATIVE_RECOVERY' if prbs_pass else 'FAIL_PRBS'
   if not combined:assert prbs_pass,'PRBS7 positive/negative/recovery qualification failed'
   if combined:run([('w',0x316,0),('w',0x315,snapshot[0x315]),('w',0x334,0),('f',0x2020),('wait',100)],'prbs-exit-to-jesd')
  if not sync_force and (not prbs or combined):
   run(writes([(0x308,0x37),(0x309,0x13),(0x30a,0x25),(0x30b,1),(0x334,0),(0x3b,0xf1),(0x3a,2),(0x300,0x0b)])+[('wait',500),('diag',)],'jesd0-enable')
   report['link_attempts']=[]
   for attempt in range(4):
    if attempt:
     run([('w',0x300,8),('wait',100),('w',0x300,11),('wait',500),('diag',)],f'jesd0-retrain-{attempt}')
    report['links']=[]
    for link in [0,1]:
     run([('w',0x300,0x0b|(link<<2))],f'jesd0-status-page-{attempt}-{link}')
     st=read([0x300,0x46c,0x46d,0x46e,0x46f,0x470,0x471,0x472,0x473,0x412,0x415,0x416,0x476,0x477,0x478,0x47c,0x47d,0x480,0x481,0x490,0x491,0x4b0,0x4b1,0x4bb]+list(range(0x400,0x40f))+list(range(0x450,0x45e)),f'jesd0-link-status-{attempt}-{link}')
     report['links'].append({hex(a):v for a,v in st.items()})
    report['link_attempts'].append(report['links'])
    if all(all(st[hex(a)]&3==3 for a in [0x470,0x471,0x472,0x473]) for st in report['links']):break
   report['link_status_pass']=all(all(st[hex(a)]&3==3 for a in [0x470,0x471,0x472,0x473]) for st in report['links'])
   if not diagnostic_rf:assert report['link_status_pass'],'JESD link status incomplete'
   if rf:
    from rf_measure import Scope
    run(writes([(8,9),(0x146,0),(0x147,8),(0x130,0x40),(0x131,0)]+[(a,0) for a in range(0x132,0x138)]+[(0x131,1),(8,0xc0),(0x1e6,0),(0x112,8),(0x3f,0)])+[('f',0x2020),('w',0x90,0),('w',0x596,4),('wait',10),('w',0x596,12),('wait',300)],'jesd0-rf-enable')
    for page in [1,8]:
     run([('w',8,page)],f'channel-dsp-page-{page}')
     dsp=read([0x130,0x131]+list(range(0x132,0x138)),f'channel-dsp-check-{page}')
     assert dsp[0x130]==0x40 and dsp[0x131]&2 and all(dsp[a]==0 for a in range(0x132,0x138)),'Channel NCO enable/zero-FTW failed'
    run([('w',8,0xc0)],'rf-main-page')
    if '--dsp-debug' in sys.argv:
     report['dsp_global']=read([0x20,0x24,0x25,0x26,0x302,0x303,0x304,0x305,0x306,0x307,0x112,0x113,0x1e6]+list(range(0x114,0x11a))+list(range(0x580,0x58e))+[0x596,0x597,0x598],'dsp-global-readback')
     report['channel_dc_sweep']=[]
     for page in [1,2,4,8,16,32]:
      run([('w',8,page),('w',0x146,0),('w',0x147,8),('w',0x148,0x20),('w',0x149,0x20),('w',0x130,0x41),('w',8,0xc0),('w',0x596,4),('wait',10),('w',0x596,12),('wait',200)],f'channel-dc-enable-{page}')
      with Scope() as scope:
       scope.io.write('CH1:SCA .1');scope.io.write('CH2:SCA .1')
       case=scope.capture(f'channel-dc-{page}',targets=[(1,76800000),(2,38400000)] if slow else None)
      report['channel_dc_sweep'].append(case)
      run([('w',8,page),('w',0x130,0x40),('w',8,0xc0)],f'channel-dc-disable-{page}')
    if '--transport-debug' in sys.argv:
     from transport_probe import probe
     report['transport_probe']=probe(run,read)
    report['rf_cases']=[]
    with Scope() as scope:
     for name,code in [('high',0x2020),('half',0x1010),('zero',0),('recovered',0x2020)]:
      run([('f',code),('wait',200)],'jesd0-payload-'+name);case=scope.capture(name,targets=[(1,76800000),(2,38400000)] if slow else None);case['payload_word']=code;report['rf_cases'].append(case)
    for ch in ['1','2']:
     high,half,zero,recovered=[case['channels'][ch] for case in report['rf_cases']]
     assert high['tone_detected'] and half['tone_detected'] and recovered['tone_detected'],'Missing RF payload tone'
     assert .4<half['fit_vpp']/high['fit_vpp']<.6,'Payload amplitude scaling mismatch'
     assert zero['fit_vpp']<high['fit_vpp']*.15,'Zero payload did not suppress RF'
     assert .85<recovered['fit_vpp']/high['fit_vpp']<1.15,'RF recovery mismatch'
    report['status']='PASS_DUAL_JESD_FPGA_PAYLOAD_RF_SCALING_ZERO_RECOVERY' if report['link_status_pass'] else 'PARTIAL_RF_PAYLOAD_PASS_LINK_STATUS_UNSTABLE'
    if combined and report['prbs_status']!='PASS':report['status']='PARTIAL_JESD_RF_PASS_PRBS_UNQUALIFIED'
    if '--leave-running' in sys.argv:
     assert report['link_status_pass'],'Will not leave unstable links running'
     report['settled_link_samples']=[]
     for sample in range(3):
      pair=[]
      for link in [0,1]:
       run([('w',0x300,11|(link<<2))],f'final-status-page-{sample}-{link}')
       status=read([0x470,0x471,0x472,0x473,0x46d,0x46e,0x46f],f'final-status-{sample}-{link}')
       pair.append({hex(a):v for a,v in status.items()})
       assert all(status[a]&3==3 for a in [0x470,0x471,0x472,0x473]) and all(status[a]&3==0 for a in [0x46d,0x46e,0x46f]),'Settled JESD link failed'
      report['settled_link_samples'].append(pair)
     run([('f',23170),('wait',200)],'leave-max-fpga-payload')
     with Scope() as scope:
      scope.io.write('CH1:SCA .2');scope.io.write('CH2:SCA .2')
      report['final_max_rf']=scope.capture('max-fpga-payload',targets=[(1,76800000),(2,38400000)] if slow else None)
     for ch,measurement in report['final_max_rf']['channels'].items():
      assert measurement['tone_detected'],'Max FPGA payload tone missing'
      expected=report['rf_cases'][0]['channels'][ch]['fit_vpp']*23170/0x2020
      assert .85<measurement['fit_vpp']/expected<1.15,'Asymmetric max payload scaling/byte order mismatch'
     report['final_max_payload_word']=23170;report['final_state']='RUNNING_VOLATILE_JESD_FPGA_PAYLOAD_INTERNAL_DC_DISABLED';leave_running=True

   else:report['status']='PASS_DUAL_JESD_LINK_STATUS_RF_NOT_YET_TESTED'
 except Exception as e:report['status']='FAIL';report['error']=str(e)
 finally:
  if changed and not leave_running:
   try:
    restore=[('w',8,0xc0),('w',0x596,4),('w',0x3f,0x30),('w',0x90,0),('w',0x300,8),('w',0x200,1)]+([('w',0x100,1)] if slow else [])
    for a,v in snapshot.items():
     if a not in [8,0x3f,0x1de,0x90,0x300,0x200]+([0x100,0x799,0x792,0xc0,0xc1,0xc7,0xdb] if slow else []):restore.append(('w',a,v))
    for link,vals in qbd.items():restore += [('w',0x300,(snapshot[0x300]&~7)|(link<<2)),('w',0x475,9)]+writes((a,v) for a,v in vals.items() if a!=0x475)+[('w',0x475,vals[0x475])]
    for page,vals in pages.items():restore += [('w',8,page)]+writes(vals.items())
    for page in [1,8]:restore += [('w',8,page),('w',0x131,0),('w',0x131,1),('wait',1)]
    if slow:
     restore += [('w',0x799,snapshot[0x799]),('w',0x792,snapshot[0x792]|2),('w',0x792,snapshot[0x792]&~2),('wait',150),('w',0xc0,snapshot[0xc0]),('w',0xdb,0),('w',0xdb,1),('w',0xdb,0),('w',0xc1,snapshot[0xc1]&~1),('w',0xc1,snapshot[0xc1]|1),('w',0xc7,snapshot[0xc7]),('wait',100)]
     run(restore,'slow-restore-muted-clock');clock=read([0x7b5,0xc3],'slow-restore-clock-check');assert clock[0x7b5]&1 and clock[0xc3]&1,'Baseline clock restore failed'
     restore=[('w',0x100,snapshot[0x100]),('w',8,0xc0),('w',0x113,0),('w',0x113,1),('w',0x596,4),('wait',10),('w',0x596,12),('wait',100)]
    restore += [('w',8,snapshot[8]),('w',0x300,snapshot[0x300]),('w',0x200,snapshot[0x200])]+([('w',0x100,snapshot[0x100])] if slow else [])+[('w',0x90,snapshot[0x90]),('w',0x3f,snapshot[0x3f]),('w',0x1de,snapshot[0x1de])]
    baseline=json.loads((ROOT/'fabric-hardware-pass-2026-10-21.json').read_text())['hmc13_before']
    restore += [('h',0x14a,0)]+[('h',int(a,16),v) for a,v in baseline.items() if int(a,16)!=0x14a]+[('h',0x14a,baseline['0x14a'])]
    run(restore,'jesd0-restore-registers');end=read([0x90,0x110,0x111,0x200,0x201,0x7b5],'jesd0-restore-check');assert all(end[a]==snapshot[a] for a in end if a!=0x7b5);assert end[0x7b5]&1;report['register_restore']='PASS'
   except Exception as e:report['restore_error']=str(e);report['status']='FAIL_RESTORE'
  if loaded and not leave_running:
   try:s.program(ROOT.parent/'spi-id.bit','jesd0-restore-probe');report['pl_restore']='PASS_SPI_PROBE'
   except Exception as e:report['pl_restore_error']=str(e);report['status']='FAIL_RESTORE'
  (ROOT/('slow6144-combined-hardware-report.json' if slow and combined else 'slow6144-prbs-hardware-report.json' if slow and prbs else 'slow6144-rf-hardware-report.json' if slow else 'sync-force-hardware-report.json' if sync_force else 'native-prbs7-all-phys-hardware-report.json' if native_prbs and all_phys else 'native-prbs7-hardware-report.json' if native_prbs else 'prbs7-hardware-report.json' if prbs else 'native-hd1-hardware-report.json' if native_hd1 else 'jesd0-rf-hardware-report.json' if rf else 'jesd0-hardware-report.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['stages','snapshot','rf_cases','link_attempts','internal_nco_clock_preview','final_max_rf','prbs_cases','settled_link_samples','channel_dc_sweep']},indent=2))
if not report['status'].startswith('PASS'):raise SystemExit(2)
