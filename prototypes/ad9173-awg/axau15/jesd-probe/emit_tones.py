"""Compile the board-independent NCO operations; model is not hardware evidence."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'control'))
from ad9172_profile import set_tones
class Emit:
 def __init__(self):self.regs={4:0x72,5:0x91,8:0xc0,0x300:11}
 def read_dac(self,a):
  v=3 if 0x470<=a<=0x473 else self.regs.get(a,0)
  print(f'checkreg {a} 255 {v}')
  return v
 def write_dac(self,a,v):
  self.regs[a]=3 if a==0x113 and v==1 else v
  print(f'dw {a} {v}')
 def wait_ms(self,t):print(f'after {t}')
set_tones(Emit())
