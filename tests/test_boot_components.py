"""Serialized boot role/gap/byte-order controls; LGPL-3.0-or-later."""
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_boot_components import verify,combine
from test_candidate_package import elf
from test_compare_bitstreams import bit


def fixture():
    fsbl=elf(True,183,0x1000,[(0x1000,b'FSBL',4)])
    pmu=elf(False,189,0x2000,[(0x2000,b'PMU!',4)])
    image=bytearray(524)
    struct.pack_into('<II',image,0x20,0xaa995566,0x584c4e58)
    struct.pack_into('<6I',image,0x2c,0x1000,512,4,4,4,4)
    struct.pack_into('<I',image,0x48,(~sum(struct.unpack_from('<10I',image,0x20)))&0xffffffff)
    struct.pack_into('<I',image,0x9c,256)
    for offset,words in [(256,[2,2,2,80,0x1000,0,0x1000,0,128,0x116,1,0,0,0,0,0]),
                         (320,[1,1,1,0,0,0,0xffffffff,0,130,0x26,1,0,0,0,1,0])]:
        words[-1]=(~sum(words[:-1]))&0xffffffff;struct.pack_into('<16I',image,offset,*words)
    image[512:]=b'PMU!FSBLAGPF'
    return image,fsbl,pmu,bit()


class BootComponents(unittest.TestCase):
    def test_valid_and_corrupted_each_component(self):
        image,fsbl,pmu,pl=fixture()
        self.assertEqual(verify(image,fsbl,pmu,pl)['status'],'SERIALIZED_BOOT_COMPONENTS_PASS')
        for offset in (512,516,520,0x48):
            bad=image.copy();bad[offset]^=1
            with self.subTest(offset=offset),self.assertRaises(ValueError):verify(bad,fsbl,pmu,pl)
        with self.assertRaises(ValueError):verify(image,fsbl,pmu,bit(payload=b'FAIL'))

    def test_zero_gap_and_overlap_rejection(self):
        data=elf(True,183,0x1000,[(0x1000,b'AB',2),(0x1004,b'CD',2)])
        self.assertEqual(combine(data,183)[2],b'AB\0\0CD')
        bad=elf(True,183,0x1000,[(0x1000,b'ABCD',4),(0x1002,b'CD',2)])
        with self.assertRaises(ValueError):combine(bad,183)
        with self.assertRaises(ValueError):combine(data,189)

if __name__=='__main__':unittest.main()
