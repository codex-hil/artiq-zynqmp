# SPDX-License-Identifier: LGPL-3.0-or-later
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pit_exception_receipt import encode,decode
class Tests(unittest.TestCase):
 def test_all_masks_routes_and_no_physical_claim(self):
  names=['msr','esr','ear','edr']
  for route in (1,2):
   for mask in range(16):
    supplied={n:(0xffffffff if i%2 else 0) for i,n in enumerate(names) if mask&(1<<i)}
    data=encode(route,supplied);r=decode(data);self.assertEqual(r['supplied_snapshots'],supplied);self.assertEqual(len(data),64)
    for name in ['session_bound','hardware_executed','deployable','pmu_ram_access_allowed','sleep_proven','recovery_proven']:self.assertFalse(r[name])
 def test_corrupt_headers_masks_reserved_invalid_words(self):
  data=encode(1,{})
  for index,value in [(0,0),(0,2),(1,0),(2,2),(3,3),(4,16)]+[(i,1) for i in range(5,16)]:
   bad=bytearray(data);struct.pack_into('<I',bad,index*4,value)
   with self.assertRaises(ValueError):decode(bytes(bad))
  for bad in [data[:-1],data+b'\0',bytearray(data),'x',b'']:
   with self.assertRaises(ValueError):decode(bad)
 def test_supplied_input_types_and_ranges(self):
  for route,values in [(True,{}),(0,{}),(3,{}),(1,{'unknown':0}),(1,{'msr':True}),(1,{'esr':-1}),(1,{'edr':2**32}),(1,[] )]:
   with self.assertRaises(ValueError):encode(route,values)
