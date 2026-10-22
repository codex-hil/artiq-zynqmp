"""Synthetic EL1 observation controls; no hardware; LGPL-3.0-or-later."""
import json,sys,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'scripts'))
from decode_ocm_environment import decode


class Environment(unittest.TestCase):
    def fixture(self):
        layout=json.loads((REPO/'evidence/ocm-environment-build-2026-10-22/layout.json').read_text())
        text='REG CurrentEL=0x4 CNTFRQ=99999000\nREG_EL1 SCTLR=0x1005 TCR=0x0 TTBR0=0x0 TTBR1=0x0\nREG_EL1 MAIR=0x0 VBAR=0xfffc0000 SP=0xfffc8000 PC=0xfffc1000\n'
        return text,layout

    def test_observation_does_not_grant_write_permission(self):
        text,layout=self.fixture();r=decode(text,layout)
        self.assertTrue(r['mmu'] and r['dcache'] and r['icache']);self.assertFalse(r['destructive_ddr_test_allowed'])

    def test_wrong_el_duplicate_or_non_ocm_stack_pc_rejected(self):
        text,layout=self.fixture()
        for bad in (text.replace('CurrentEL=0x4','CurrentEL=0xc'),text+'REG_EL1 SCTLR=0x0\n',text.replace('SP=0xfffc8000','SP=0x20200000'),text.replace('PC=0xfffc1000','PC=0x100000')):
            with self.assertRaises(ValueError):decode(bad,layout)

if __name__=='__main__':unittest.main()
