"""Optional diagnostic integration/CSR ABI controls; LGPL-3.0-or-later."""
import sys,json,tempfile,unittest
from pathlib import Path
from migen import Signal
from migen.fhdl import verilog
from litex.soc.interconnect.axi import AXIInterface
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'boards/genesys_zu-5ev/1_gateware'))
from local_rtio import LocalRTIO
class Tests(unittest.TestCase):
 def design(self,enabled):
  b=AXIInterface(data_width=64,address_width=49,id_width=6)
  return LocalRTIO(Signal(),Signal(),b,analyzer=True,dma_observer=enabled)
 def test_optional_map_preserves_all_existing_registers(self):
  maps=[]
  for enabled in [False,True]:
   dut=self.design(enabled)
   with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'map.json';dut.write_map(p);maps.append(json.loads(p.read_text())['registers'])
   if enabled:
    self.assertTrue(all(c.__class__.__name__=='CSRStatus' for c in dut.dma_observer.get_csrs()))
    rtl=str(verilog.convert(dut,ios=set()))
    self.assertIn('module',rtl)
  old,new=maps
  self.assertEqual({n:new[n] for n in old},old)
  added=set(new)-set(old)
  self.assertEqual(added,{'dma_observer_outstanding','dma_observer_flags'})
  self.assertEqual(new['dma_observer_outstanding']['address'],0xa0003000)
  self.assertEqual(new['dma_observer_flags']['address'],0xa0003004)
 def test_no_dma_rejects(self):
  with self.assertRaises(ValueError):LocalRTIO(Signal(),Signal(),dma_observer=True)
if __name__=='__main__':unittest.main()
