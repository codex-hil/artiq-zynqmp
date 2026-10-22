"""Controller decoder fixture guards, not hardware; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from decode_ddr_config import decode,REGISTERS


class DDRConfig(unittest.TestCase):
    def log(self,mstr=0x43001010):
        values={k:0 for k in REGISTERS};values['MSTR']=mstr
        return '\n'.join(f'DDR_CONFIG {k} 0x{a:08x} 0x{values[k]:08x}' for k,a in REGISTERS.items())+'\nTEST ddr_config_snapshot PASS\n'

    def test_fields_are_controller_view_not_capacity(self):
        r=decode(self.log());self.assertTrue(r['ddr4']);self.assertEqual(r['active_ranks'],2)
        self.assertEqual(r['device_dq_bits'],8);self.assertEqual(r['bus_width_proportion'],'half')
        self.assertEqual(r['physical_capacity'],'NOT_ESTABLISHED')

    def test_incomplete_duplicate_wrong_address_reserved_rejected(self):
        good=self.log()
        for log in (good.replace('DDR_CONFIG MSTR','OTHER MSTR'),good+'DDR_CONFIG MSTR 0xfd070000 0x43001010\n',good.replace('0xfd070200','0xfd070204'),self.log(0x40003010),self.log(0x40000010)):
            with self.subTest(log=log[:60]),self.assertRaises(ValueError):decode(log)

if __name__=='__main__':unittest.main()
