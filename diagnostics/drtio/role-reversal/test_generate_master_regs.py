"""Exact map/profile refusal controls; LGPL-3.0-or-later."""
import copy,json,tempfile,unittest
from pathlib import Path
from generate_master_regs import generate
ROOT=Path(__file__).resolve().parents[3]
MAP=ROOT/'evidence/genesys-master-csr-offline-2026-11-07/csr-map.json'
class RegisterGeneratorTests(unittest.TestCase):
    def test_generated_header_reproduces(self):
        self.assertEqual(generate(MAP),(Path(__file__).parent/'a53/master_regs.h').read_text())
    def test_profile_and_register_mutations_refused(self):
        original=json.loads(MAP.read_text());controls=[]
        for field,value in [('kind','local-rtio'),('identity',0),('fine_ts_width',0),('timestamp_unit_ps',8000),('coarse_hz',150000000),('csr_base',0)]:
            m=copy.deepcopy(original);m[field]=value;controls.append(m)
        for field,value in [('bits',32),('words',1),('word_order','little'),('word_bytes',8),('address',0xa0000001),('address',0xa0002000),('address',original['registers']['kernel_target']['address'])]:
            m=copy.deepcopy(original);m['registers']['kernel_now'][field]=value;controls.append(m)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'mutated.json'
            for i,m in enumerate(controls):
                with self.subTest(control=i):
                    p.write_text(json.dumps(m))
                    with self.assertRaises(ValueError):generate(p)
if __name__=='__main__':unittest.main()
