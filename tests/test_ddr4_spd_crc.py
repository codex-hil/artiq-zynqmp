"""DDR4 base CRC acceptance, corruption and downstream gates; LGPL-3.0-or-later."""
import binascii,subprocess,sys,tempfile,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'scripts'))
from check_ddr4_spd_crc import verify
from decode_ddr4_spd import decode
from compare_ddr_geometry import compare

def fixture():
    d=bytearray(128);d[0]=0x23;d[1]=0x11;d[2]=12;d[3]=3;d[4]=0x45;d[5]=0x21;d[12]=2;d[13]=3
    d[126:128]=bytes.fromhex('8df1');return d

class BaseCRC(unittest.TestCase):
    def test_known_primitive_vector_and_synthetic_spd(self):
        self.assertEqual(binascii.crc_hqx(b'123456789',0),0x31c3)
        r=verify(fixture());self.assertTrue(r['valid']);self.assertEqual(r['computed'],'0xf18d')
        self.assertEqual(r['covered_bytes'],126);self.assertFalse(r['destructive_test_allowed'])
    def test_every_single_bit_in_base_block_detected(self):
        for byte in range(128):
            for bit in range(8):
                d=fixture();d[byte]^=1<<bit
                with self.subTest(byte=byte,bit=bit):
                    try:r=verify(d)
                    except ValueError:continue
                    self.assertFalse(r['valid'])
    def test_unsupported_truncated_endianness_and_coverage(self):
        for d in (fixture()[:127],bytearray(128)):
            with self.assertRaises(ValueError):verify(d)
        d=fixture();d[0]|=128
        with self.assertRaises(ValueError):verify(d)
        d=fixture();d[126:128]=d[126:128][::-1];self.assertFalse(verify(d)['valid'])
        d=fixture();d[125]^=1;self.assertFalse(verify(d)['valid'])
        d=fixture()+bytearray(128);d[200]^=1;self.assertTrue(verify(d)['valid'])
    def test_decode_compare_and_cli_reject_bad_crc(self):
        d=fixture();snapshot=(REPO/'evidence/ddrc-snapshot-2026-10-22/snapshot.log').read_text()
        self.assertEqual(decode(d,require_crc=True)['crc'],'BASE_VALID')
        r=compare(d,snapshot,require_crc=True);self.assertTrue(r['geometry_matches']);self.assertFalse(r['destructive_test_allowed'])
        d[100]^=1
        for fn in (lambda:decode(d,require_crc=True),lambda:compare(d,snapshot,require_crc=True)):
            with self.assertRaisesRegex(ValueError,'CRC'):fn()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'spd.bin').write_bytes(d)
            r=subprocess.run([sys.executable,str(REPO/'scripts/check_ddr4_spd_crc.py'),'--spd',str(root/'spd.bin'),'--output',str(root/'report.json')],capture_output=True,text=True)
            self.assertEqual(r.returncode,1);self.assertIn('DDR4_BASE_CRC_FAIL',(root/'report.json').read_text())

if __name__=='__main__':unittest.main()
