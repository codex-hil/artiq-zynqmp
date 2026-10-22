"""OCM ELF/layout boundary controls; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_ocm_image import check
from test_candidate_package import elf


class OCM(unittest.TestCase):
    def fixture(self):
        data=elf(True,183,0xfffc0000,[(0xfffc0000,b'code',0x9000)])
        symbols='\n'.join(f'{a:x} T {s}' for a,s in [(0xfffc0000,'__ocm_start'),(0xfffc0000,'__vectors'),(0xfffc4000,'__bss_start'),(0xfffc4010,'__bss_end'),(0xfffc9000,'__stack0_end')]);return data,symbols

    def test_layout_only_not_runtime_permission(self):
        data,symbols=self.fixture();r=check(data,symbols)
        self.assertFalse(r['destructive_ddr_test_allowed']);self.assertEqual(r['mmu_cache_state'],'NOT_PROVEN')

    def test_ddr_segment_missing_stack_and_wrong_entry_rejected(self):
        data,symbols=self.fixture()
        cases=[(elf(True,183,0xfffc0000,[(0xfffc0000,b'code',0x9000),(0x100000,b'data',4)]),symbols),(data,symbols.replace('__stack0_end','other')),(elf(True,183,0x100000,[(0x100000,b'code',0x9000)]),symbols)]
        for data,symbols in cases:
            with self.assertRaises(ValueError):check(data,symbols)

if __name__=='__main__':unittest.main()
