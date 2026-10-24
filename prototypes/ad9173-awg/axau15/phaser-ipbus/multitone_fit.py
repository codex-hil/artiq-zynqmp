"""Five-tone RF acceptance from actual scope samples, never simulated data."""
import numpy as np
from scipy.optimize import minimize_scalar

def validate_multitone(capture,full,reference=None):
 for ch,v in capture['channels'].items():
  y=np.array(v['curve']);t=np.arange(len(y))*v['sample_interval_s']
  nominal=np.array([145,147,149,151,153])*1e6
  def fit(scale):
   angle=2*np.pi*t[:,None]*nominal[None,:]*scale
   mat=np.column_stack([np.cos(angle),np.sin(angle),np.ones(len(t))])
   coef=np.linalg.lstsq(mat,y,rcond=None)[0]
   return np.mean((y-mat@coef)**2),2*np.hypot(coef[:5],coef[5:10]),np.arctan2(-coef[5:10],coef[:5])
  best=minimize_scalar(lambda scale:fit(scale)[0],bounds=(.9999,1.0001),method='bounded',options={'xatol':1e-10})
  error,vpp,phase=fit(best.x)
  curvature=np.angle(np.exp(1j*(phase[:-2]-2*phase[1:-1]+phase[2:])))
  ratios=vpp/full['channels'][ch]['fit_vpp']
  assert not v['clipped']
  assert np.all(abs(ratios-.08/(32767/32768))<.015),(ch,ratios)
  assert np.sqrt(error)<.008,(ch,error)
  v['multitone']={'frequencies_hz':(nominal*best.x).tolist(),'vpp':vpp.tolist(),'ratios_to_single_full':ratios.tolist(),'residual_rms':float(np.sqrt(error)),'phase_curvature_rad':curvature.tolist()}
  if reference is not None:
   previous=np.array(reference['channels'][ch]['multitone']['phase_curvature_rad'])
   delta=np.angle(np.exp(1j*(curvature-previous)))
   expected=np.array([np.pi/2,-np.pi,np.pi/2])
   phase_error=np.angle(np.exp(1j*(delta-expected)))
   assert np.max(abs(phase_error))<.3,(ch,delta,phase_error)
   v['multitone']['phase_change_error_rad']=phase_error.tolist()
