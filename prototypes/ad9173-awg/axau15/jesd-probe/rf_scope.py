"""CH3/4-only static RF measurement. Caller holds shared MSO4104 lease.
No trigger, acquisition or horizontal writes; CH1/2 settings stay untouched.
"""
import sys,time
import numpy as np
from scipy.optimize import minimize_scalar
sys.path.insert(0,'/home/codex-hil/lab-instruments')
from labinstruments.transport import Transport
from labinstruments.drivers import Driver

class Scope:
 def __enter__(self):
  self.io=Transport(dict(kind='tcp',host='192.168.2.15',port=4000,timeout=4))
  self.io.__enter__();self.saved={}
  try:
   self.identity=Driver(self.io,'mso4104','C020817').identify()
   keys=['HEADER','CH3:SCA','CH4:SCA','CH3:POS','CH4:POS','CH3:OFFS','CH4:OFFS',
         'DATA:SOURCE','DATA:ENCDG','DATA:WIDTH','DATA:START','DATA:STOP']
   self.saved={k:self.io.query(k+'?') for k in keys}
   if self.saved['HEADER']!='0':raise ValueError('Expected header-off state')
   self.untouched={k:self.io.query(k+'?') for k in ['CH1:SCA','CH2:SCA','HOR:SCA','HOR:RECORDLENGTH','TRIG:A:MOD','ACQ:STATE','CH3:TER','CH4:TER','SELECT:CH3','SELECT:CH4']}
   if self.untouched['ACQ:STATE']!='1' or self.untouched['TRIG:A:MOD']!='AUTO':raise ValueError('Continuous auto acquisition required')
   if any(float(self.untouched[f'CH{c}:TER'])!=50 or self.untouched[f'SELECT:CH{c}']!='1' for c in (3,4)):raise ValueError('CH3/4 must be selected and 50 ohm')
   for c in (3,4):
    for key,val in [('SCA','.1'),('POS','0'),('OFFS','0')]:self.io.write(f'CH{c}:{key} {val}')
   return self
  except BaseException:
   self.__exit__(None,None,None);raise
 def __exit__(self,*args):
  try:
   for k,v in self.saved.items():self.io.write(k+' '+v)
  finally:self.io.__exit__(*args)
 def capture(self,label):
  io=self.io;time.sleep(.4)
  result={'label':label,'identity':self.identity,'channels':{}}
  for ch,target in [(3,149e6),(4,151e6)]:
   io.write(f'DATA:SOURCE CH{ch}')
   for c in ['DATA:ENCDG ASCII','DATA:WIDTH 1','DATA:START 1','DATA:STOP 10000']:io.write(c)
   sc={a:float(io.query('WFMO:'+a+'?')) for a in ['XINCR','YMULT','YZERO','YOFF']}
   raw=np.array([float(v) for v in io.query('CURVE?').split(',')])
   if len(raw)<1000 or sc['XINCR']>=1/(2*target):raise ValueError('Insufficient sampling')
   y=(raw-sc['YOFF'])*sc['YMULT']+sc['YZERO'];t=np.arange(len(y))*sc['XINCR']
   def fit(f):
    mat=np.column_stack([np.cos(2*np.pi*f*t),np.sin(2*np.pi*f*t),np.ones(len(t))])
    coef=np.linalg.lstsq(mat,y,rcond=None)[0]
    return float(np.mean((y-mat@coef)**2)),coef
   # Grid avoids local minima when fitting hundreds of cycles.
   grid=np.linspace(target-500e3,target+500e3,81)
   idx=int(np.argmin([fit(f)[0] for f in grid]))
   step=grid[1]-grid[0]
   best=minimize_scalar(lambda f:fit(f)[0],bounds=(grid[idx]-step,grid[idx]+step),method='bounded')
   error,coef=fit(best.x)
   result['channels'][str(ch)]={'fit_hz':float(best.x),'fit_vpp':float(2*np.hypot(*coef[:2])),
    'residual_rms':float(np.sqrt(error)),'clipped':bool(np.max(np.abs(raw))>=125),
    'sample_interval_s':sc['XINCR'],'raw_peak_to_peak':float(np.ptp(y)),'curve':y.tolist()}
  return result

def validate(capture,previous):
 label=capture['label']
 for ch,v in capture['channels'].items():
  if v['clipped']:raise ValueError(f'CH{ch} clipped')
  if label in ('baseline','zero'):
   limit=.005 if 'full' not in previous else max(.005,.03*previous['full']['channels'][ch]['fit_vpp'])
   if v['fit_vpp']>limit:raise ValueError(f'CH{ch} residual tone at zero')
  else:
   if abs(v['fit_hz']-({'3':149e6,'4':151e6}[ch]))>50e3:raise ValueError(f'CH{ch} frequency mismatch')
   if v['fit_vpp']<.03 or v['residual_rms']>v['fit_vpp']*.15:raise ValueError(f'CH{ch} no clean tone')
   if label!='full':
    ratio=v['fit_vpp']/previous['full']['channels'][ch]['fit_vpp']
    target={'half':16384/32767,'recovered':1,'asymmetric':23170/32767,'final':1}[label]
    v['ratio_to_full']=ratio
    if abs(ratio-target)>.05:raise ValueError(f'CH{ch} amplitude ratio {ratio} expected {target}')
