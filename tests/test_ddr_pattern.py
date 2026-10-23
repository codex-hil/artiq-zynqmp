"""Executable host-model pattern/fault controls, no HW. LGPL-3.0-or-later."""
import ctypes as C,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WRITE=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_uint64)
READ=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.POINTER(C.c_uint64))
BARRIER=C.CFUNCTYPE(C.c_int,C.c_void_p)
class IO(C.Structure):_fields_=[('context',C.c_void_p),('write',WRITE),('read',READ),('barrier',BARRIER)]
class Report(C.Structure):_fields_=[(n,C.c_uint64) for n in ['writes','reads','address','expected','actual']]+[('phase',C.c_uint32),('error',C.c_uint32)]
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();lib=Path(cls.tmp.name)/'pattern.so'
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-shared','-fPIC',str(ROOT/'diagnostics/ddr/bounded_test/pattern.c'),'-o',str(lib)],check=True)
  cls.lib=C.CDLL(str(lib));cls.lib.ddr_pattern.argtypes=[C.POINTER(C.c_uint64),C.c_uint32,C.POINTER(IO),C.POINTER(Report)]
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def run_model(self,addresses,fault=None,alias=False):
  memory={};calls=[]
  def key(a):return 0 if alias else a
  def write(_,a,v):
   calls.append(('w',a));memory[key(a)]=v;return int(fault=='write')
  def read(_,a,v):
   calls.append(('r',a));v[0]=memory.get(key(a),0);return int(fault=='read')
  def barrier(_):calls.append(('b',));return int(fault=='barrier')
  io=IO(None,WRITE(write),READ(read),BARRIER(barrier));r=Report();array=(C.c_uint64*len(addresses))(*addresses)
  code=self.lib.ddr_pattern(array,len(addresses),C.byref(io),C.byref(r));return code,r,calls
 def test_both_windows_and_full_write_before_read(self):
  code,r,calls=self.run_model([0x40000000,0x7ffffff8,0x800000000,0x87ffffff8])
  self.assertEqual(code,0);self.assertEqual((r.writes,r.reads),(16,16))
  self.assertEqual([c[0] for c in calls[:9]],list('wwwwbrrrr'))
 def test_gap_overflow_alignment_and_duplicate_no_io(self):
  for addresses in [[],[0x80000000],[0x7fffffff8],[0x880000000],[0x40000001],[0,0],list(range(0,8193*8,8))]:
   code,r,calls=self.run_model(addresses);self.assertEqual(code,1);self.assertEqual(calls,[])
 def test_alias_detected_in_address_phase(self):
  code,r,_=self.run_model([0x40000000,0x800000000],alias=True)
  self.assertEqual(code,5);self.assertEqual(r.phase,2);self.assertNotEqual(r.expected,r.actual)
 def test_faults_stop_bounded(self):
  for fault,expected,n in [('write',2,1),('barrier',3,3),('read',4,4)]:
   code,r,calls=self.run_model([0,8],fault=fault);self.assertEqual(code,expected);self.assertEqual(len(calls),n)
if __name__=='__main__':unittest.main()
