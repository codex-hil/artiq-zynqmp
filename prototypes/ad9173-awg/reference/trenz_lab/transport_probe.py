"""Constant-sample receiver comparator probe, not full unique-sample STPL qualification."""
def probe(run, read):
 results=[]
 for payload in [0x2020,0x1010,0,0x2020]:
  run([('f',payload),('wait',100)],f'tpl-payload-{payload}')
  for iq in [0,1]:
   for wrong in [False,True]:
    expected=(payload if iq==0 else 0) ^ (1 if wrong else 0)
    ops=[('w',0x32c,0),('w',0x32f,iq<<6),('w',0x32d,expected&255),('w',0x32e,expected>>8),('w',0x32c,1),('w',0x32c,3),('w',0x32c,1),('wait',20),('w',0x32c,0),('r',0x32f)]
    r=run(ops,f'tpl-check-{payload}-{iq}-{int(wrong)}')
    result=r['operations'][-1]['value']
    results.append({'payload':payload,'iq':iq,'wrong_reference':wrong,'reference':expected,'status':result,'failed':bool(result&1)})
 return {'kind':'CONSTANT_SAMPLE_COMPARATOR_DIAGNOSTIC_NOT_FULL_STPL','cases':results,'qualified':all(c['failed']==c['wrong_reference'] for c in results)}
