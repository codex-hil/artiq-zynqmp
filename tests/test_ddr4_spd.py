"""SPD geometry consistency and AMD C parity, synthetic fixtures; LGPL-3.0-or-later."""
import ctypes,re,subprocess,sys,tempfile,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'scripts'))
from decode_ddr4_spd import decode


def spd():
    d=bytearray(128);d[2]=12;d[3]=3;d[4]=0x45;d[5]=0x21;d[12]=2;d[13]=3;return d


class SPD(unittest.TestCase):
    def test_synthetic_four_gib_and_source_rank_size(self):
        d=spd();r=decode(d);self.assertEqual(r['module_bytes'],4*1024**3);self.assertFalse(r['destructive_test_allowed'])
        source=(REPO/'boards/genesys_zu-5ev/3_bootable/xfsbl_ddr_init.c').read_text()
        fn=re.search(r'u64 XFsbl_ComputeDdr4RankSize\([^\n]+\)\n\{.*?\n\}',source,re.S)[0]
        c='typedef unsigned char u8;typedef unsigned int u32;typedef unsigned long long u64;\n'
        c+='struct Ddr4SpdEeprom {u8 InfoSizeCrc,SpdRev,MemType,ModuleType,DensityBanks,Addressing,PackageType,OptFeature,ThermalRef,OthOptFeatures,Res10,ModuleVdd,Organization,BusWidth;};\n'+fn
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'source.c').write_text(c);subprocess.run(['cc','-shared','-fPIC',str(p/'source.c'),'-o',str(p/'source.so')],check=True)
            f=ctypes.CDLL(str(p/'source.so')).XFsbl_ComputeDdr4RankSize;f.restype=ctypes.c_uint64
            buf=(ctypes.c_ubyte*len(d)).from_buffer_copy(d);self.assertEqual(f(buf),r['rank_bytes'])

    def test_truncated_stacked_reserved_and_inconsistent_rejected(self):
        for offset,value in [(2,11),(6,0x82),(12,0x42),(4,0x4f),(13,7),(5,0x19)]:
            d=spd();d[offset]=value
            with self.subTest(offset=offset),self.assertRaises(ValueError):decode(d)
        with self.assertRaises(ValueError):decode(spd()[:14])

if __name__=='__main__':unittest.main()
