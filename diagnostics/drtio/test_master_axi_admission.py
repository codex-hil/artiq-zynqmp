# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from migen.sim import run_simulation
from litex.soc.interconnect.axi import AXIInterface
from master_axi_admission import MasterAXIAdmission

class AdmissionTests(unittest.TestCase):
    def test_all_channels_block_and_forward(self):
        target=AXIInterface(data_width=32,address_width=40,id_width=16)
        gate=MasterAXIAdmission(target)
        def test():
            for name in ('aw','w','ar','b','r'):
                source,sink=((getattr(target,name),getattr(gate.axi,name))
                             if name in ('b','r') else
                             (getattr(gate.axi,name),getattr(target,name)))
                yield source.valid.eq(1)
                yield sink.ready.eq(1)
            for enabled in (0,1,0):
                yield gate.enable.eq(enabled)
                yield
                for name in ('aw','w','ar','b','r'):
                    source,sink=((getattr(target,name),getattr(gate.axi,name))
                                 if name in ('b','r') else
                                 (getattr(gate.axi,name),getattr(target,name)))
                    self.assertEqual((yield source.ready),enabled)
                    self.assertEqual((yield sink.valid),enabled)
        run_simulation(gate,test())

    def test_wrong_interface_refused(self):
        with self.assertRaises(ValueError):
            MasterAXIAdmission(AXIInterface(data_width=32,address_width=32,id_width=1))

if __name__=='__main__':unittest.main()
