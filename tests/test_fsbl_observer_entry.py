"""Synthetic terminal admission controls; LGPL-3.0-or-later."""
import copy
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_fsbl_observer_entry import descriptor, admit
from test_el3_observer import fixture


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()
        struct.pack_into('<II', self.data, 120, 0xd503205f, 0x17ffffff)
        self.symbols = '00000000fffc0000 t XFsbl_Loop\n'
        self.desc = descriptor(self.data, self.symbols)
        sample = dict(pc=0xfffc0000, currentel=12, sctlr_el3=0, daif=0x3c0,
                      mpidr_el1=0x80000000, suspended=True, cable='210383B7F02DA', core='Cortex-A53 #0')
        self.capture = dict(fsbl_sha256=self.desc['fsbl_sha256'], samples=[sample, dict(sample)])

    def test_consistent_not_execution_proof(self):
        self.assertFalse(admit(self.desc, self.capture)['hardware_executed'])

    def test_negative_states(self):
        for field, value in [('pc',0xfffc0008),('currentel',4),('sctlr_el3',4),('sctlr_el3',1),('sctlr_el3',4096),('daif',0x1c0),('suspended',False),('cable','other'),('core','Cortex-A53 #1'),('mpidr_el1',1),('pc',True)]:
            with self.subTest(field=field,value=value):
                c=copy.deepcopy(self.capture)
                for s in c['samples']: s[field]=value
                with self.assertRaises(ValueError): admit(self.desc,c)
        c=copy.deepcopy(self.capture);c['samples'][1]['pc']+=4
        with self.assertRaises(ValueError): admit(self.desc,c)
        c=copy.deepcopy(self.capture);c['fsbl_sha256']='wrong'
        with self.assertRaises(ValueError): admit(self.desc,c)

    def test_symbol_and_instruction_checks(self):
        for text in ('', self.symbols*2):
            with self.assertRaises(ValueError): descriptor(self.data,text)
        self.data[120]=0
        with self.assertRaises(ValueError): descriptor(self.data,self.symbols)


if __name__ == '__main__': unittest.main()
