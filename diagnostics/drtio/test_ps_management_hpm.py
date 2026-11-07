# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from types import SimpleNamespace
from migen import Module,Signal
from litex.soc.interconnect.axi import AXIInterface
from ps_management_hpm import connect_management_hpm1

class HPMTests(unittest.TestCase):
    def fixture(self):
        axi=AXIInterface(data_width=32,address_width=40,id_width=16)
        ps=SimpleNamespace(inputs={'maxihpm1_fpd_aclk':Signal()},outputs={})
        for channel,names in {'aw':'id addr len size burst lock cache prot qos valid ready',
            'ar':'id addr len size burst lock cache prot qos valid ready','w':'data strb last valid ready',
            'b':'id resp valid ready','r':'id data resp last valid ready'}.items():
            for field in names.split():
                input_pin=(field=='ready' if channel in ('aw','w','ar') else field!='ready')
                collection=ps.inputs if input_pin else ps.outputs
                collection['maxigp1_'+channel+field]=Signal(len(getattr(getattr(axi,channel),field)))
        return ps,axi
    def test_complete_declared_export(self):
        ps,axi=self.fixture();d=Module()
        connect_management_hpm1(d,ps,axi,Signal())
        self.assertEqual(len(d._fragment.comb),38)
    def test_actual_dell_export(self):
        from pathlib import Path
        path=Path(__file__).resolve().parents[2]/'evidence/genesys-master-aux-gray-link-2026-11-07/ps-hpm-wrapper-v2/pins.tsv'
        ps=SimpleNamespace(inputs={},outputs={})
        for line in path.read_text().splitlines():
            name,direction,left,right=line.split('\t')
            width=abs(int(left)-int(right))+1 if left and right else 1
            collection=ps.inputs if direction=='I' else ps.outputs
            collection[name]=Signal(width)
        axi=AXIInterface(data_width=32,address_width=40,id_width=16)
        d=Module()
        connect_management_hpm1(d,ps,axi,Signal())
        self.assertEqual(len(d._fragment.comb),38)

    def test_export_mismatch_no_partial_wiring(self):
        for kind in ('missing','width','direction','clock'):
            ps,axi=self.fixture();d=Module()
            if kind=='missing':del ps.outputs['maxigp1_awaddr']
            if kind=='width':ps.outputs['maxigp1_awaddr']=Signal(32)
            if kind=='direction':ps.inputs['maxigp1_awaddr']=ps.outputs.pop('maxigp1_awaddr')
            if kind=='clock':del ps.inputs['maxihpm1_fpd_aclk']
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                connect_management_hpm1(d,ps,axi,Signal())
            self.assertEqual(len(d._fragment.comb),0)

if __name__=='__main__':unittest.main()
