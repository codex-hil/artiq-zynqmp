"""Expected model BRK mode controls; LGPL-3.0-or-later."""
import json,re,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from check_ddr_ocm_model import parse,preflight
class Tests(unittest.TestCase):
 def frame(self):
  regs={'x0':12,'x14':4,'x15':0xf3,'x16':12,'x17':0xf2000053,'x18':0,'x19':0xfffc8880,'x20':0x2cd,'x21':0x2c0}
  return '\n'.join(['DDR_MODEL_BEGIN','DDR_MODEL_PC '+str(0xfffc88b4)]+['DDR_MODEL_REG '+n+' '+str(v) for n,v in regs.items()]+[f'DDR_MODEL_REPORT {i} 0x00000000' for i in range(12)]+['DDR_MODEL_RESULT 0x00000000','DDR_MODEL_END'])
 def test_exact_brk_and_wrong_esr_slot_terminal(self):
  text=self.frame();self.assertFalse(parse(text,'brk')['destructive_test_allowed'])
  with self.assertRaises(ValueError):parse(text)
  for old,new in [('x14 4','x14 5'),('x19 '+str(0xfffc8880),'x19 0'),('x17 '+str(0xf2000053),'x17 0'),('REPORT 0 0x00000000','REPORT 0 0x00000001')]:
   with self.assertRaises(ValueError):parse(text.replace(old,new),'brk')
 def test_brk_binary_cannot_be_selected_as_normal(self):
  p=ROOT/'evidence/ddr-model-brk-integration-2026-10-23/model-inputs.json';preflight(p,ROOT)
  m=json.loads(p.read_text());m['mode']='normal'
  with tempfile.TemporaryDirectory() as tmp:
   q=Path(tmp)/'bad.json';q.write_text(json.dumps(m))
   with self.assertRaises(ValueError):preflight(q,ROOT)
if __name__=='__main__':unittest.main()
