"""Tek MSO4104 waveform measurements; caller holds shared scope lease."""
import sys,time
import numpy as np
from scipy.optimize import minimize_scalar
sys.path.insert(0,'/home/codex-hil/workspaces/lab-instruments')
from labinstruments.transport import Transport
from labinstruments.drivers import Driver
class Scope:
 def __enter__(self):
  self.io=Transport({'kind':'tcp','host':'192.168.2.15','port':4000,'timeout':4});self.io.__enter__();self.driver=Driver(self.io,'mso4104','C020817');self.identity=self.driver.identify()
  keys=['CH1:SCA','CH2:SCA','CH1:POS','CH2:POS','CH1:OFFS','CH2:OFFS','HOR:SCA','TRIG:A:MOD','ACQ:STATE','DATA:SOURCE','DATA:ENCDG','DATA:START','DATA:STOP']
  self.saved={k:self.io.query(k+'?') for k in keys}
  for c in ['HEADER OFF','CH1:SCA .05','CH2:SCA .05','CH1:POS 0','CH2:POS 0','CH1:OFFS 0','CH2:OFFS 0','HOR:SCA 20e-9','TRIG:A:MOD AUTO','ACQ:STATE RUN']:self.io.write(c)
  return self
 def __exit__(self,*args):
  try:
   for k,v in self.saved.items():self.io.write(k+' '+v)
  finally:self.io.__exit__(*args)
 def capture(self,label,targets=None):
  result={'label':label,'identity':self.identity,'channels':{}};io=self.io;time.sleep(.25)
  for ch,target in (targets or [(1,92160000),(2,46080000)]):
   io.write(f'DATA:SOURCE CH{ch}');io.write('DATA:ENCDG ASCII');io.write('DATA:START 1');io.write('DATA:STOP 1000')
   sc={a:float(io.query('WFMO:'+a+'?')) for a in ['XINCR','YMULT','YZERO','YOFF']};raw=np.array([float(v) for v in io.query('CURVE?').split(',')]);y=(raw-sc['YOFF'])*sc['YMULT']+sc['YZERO'];t=np.arange(len(y))*sc['XINCR']
   def fit(f):
    a=np.column_stack([np.cos(2*np.pi*f*t),np.sin(2*np.pi*f*t),np.ones(len(t))]);coef=np.linalg.lstsq(a,y,rcond=None)[0];return np.mean((y-a@coef)**2),coef
   best=minimize_scalar(lambda f:fit(f)[0],bounds=(target-1e6,target+1e6),method='bounded');error,coef=fit(best.x);amp=float(np.hypot(*coef[:2]));noise=float(np.sqrt(error))
   result['channels'][str(ch)]={'expected_hz':target,'fit_hz':float(best.x),'fit_vpp':amp*2,'residual_rms':noise,'tone_detected':bool(amp>.002 and amp>5*noise),'raw_peak_to_peak':float(y.max()-y.min()),'curve':y.tolist(),'sample_interval_s':sc['XINCR']}
  return result
