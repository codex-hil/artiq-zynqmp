"""Bit metadata/payload separation controls, no HW; LGPL-3.0-or-later."""
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compare_bitstreams import parse,compare


def bit(date=b'2026/10/21',payload=b'FPGA'):
    def string(x):return struct.pack('>H',len(x))+x
    return string(bytes.fromhex('0ff00ff00ff00ff000'))+b'\0\1'+b''.join(bytes([tag])+string(value+b'\0') for tag,value in zip(b'abcd',(b'top',b'xczu5ev',date,b'12:00:00')))+b'e'+struct.pack('>I',len(payload))+payload


class BitTests(unittest.TestCase):
    def test_metadata_difference_does_not_hide_payload_difference(self):
        self.assertEqual(compare(bit(),bit(date=b'2026/10/22'))['status'],'CONFIGURATION_BYTES_IDENTICAL')
        self.assertEqual(compare(bit(),bit(payload=b'FAIL'))['status'],'CONFIGURATION_BYTES_DIFFER')

    def test_bad_format_and_truncation_rejected(self):
        for data in (b'not-bit',bit()[:-1],bit()+b'extra',bit().replace(b'\0\1a',b'\0\1z',1)):
            with self.subTest(data=data[:12]),self.assertRaises(ValueError):parse(data)

if __name__=='__main__':unittest.main()
