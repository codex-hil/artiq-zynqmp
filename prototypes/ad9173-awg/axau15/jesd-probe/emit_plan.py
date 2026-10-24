"""Offline compiler: emit guarded Tcl transactions from the portable DAC profile.
The model below only chooses expected values for guard generation, not HW evidence.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'control'))
from ad9172_profile import configure_links,prepare_fpga_dsp
class Emit:
 def read_dac(self,a):
  v={4:0x72,5:0x91,0x7b5:1,0xc3:1,0x799:5,0x110:0x23,0x111:0x82,0x281:1,8:0xc0,0x130:0x40,0x131:2}.get(a,0)
  mask={0x7b5:1,0xc3:1,0x281:1,0x799:63,0x131:2}.get(a,255)
  print(f'checkreg {a} {mask} {v}')
  return v
 def write_dac(self,a,v):print(f'dw {a} {v}')
 def wait_ms(self,t):print(f'after {t}')
configure_links(Emit());prepare_fpga_dsp(Emit())
