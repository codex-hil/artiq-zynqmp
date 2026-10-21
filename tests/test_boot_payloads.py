"""PHT bounds/checksum and payload controls; no hardware; LGPL-3.0-or-later."""
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_boot_payloads import partitions,match


def image(next_header=0):
    data=bytearray(516);struct.pack_into('<II',data,0x20,0xaa995566,0x584c4e58);struct.pack_into('<I',data,0x9c,0x100)
    words=[1,1,1,next_header,0x20200000,0,0x20200000,0,0x80,0x216,1,0,0,0,0,0]
    words[-1]=(~sum(words[:-1]))&0xffffffff;struct.pack_into('<16I',data,0x100,*words);data[512:]=b'data';return data


class BootPayloadTests(unittest.TestCase):
    def test_valid_chain_and_payload(self):
        parts=partitions(image());r=match(parts,[dict(address=0x20200000,filesz=4,payload=b'data')],2,'worker')
        self.assertEqual(r[0]['bytes'],4)

    def test_header_corruption_cycle_and_truncation_rejected(self):
        bad=image();bad[0x100]^=1
        for data in (bad,image(0x40),image()[:-1]):
            with self.subTest(data=data[:8]),self.assertRaises(ValueError):partitions(data)

    def test_data_corruption_and_wrong_cpu_rejected(self):
        data=image();data[-1]^=1;expected=[dict(address=0x20200000,filesz=4,payload=b'data')]
        with self.assertRaises(ValueError):match(partitions(data),expected,2,'worker')
        with self.assertRaises(ValueError):match(partitions(image()),expected,1,'worker')

if __name__=='__main__':unittest.main()
