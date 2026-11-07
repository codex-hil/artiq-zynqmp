# SPDX-License-Identifier: LGPL-3.0-or-later
import unittest
from pathlib import Path
from types import SimpleNamespace
from migen import Signal
from raw20_codec import Raw20Codec
from master_integration import GenesysMasterIntegration

class IntegrationTests(unittest.TestCase):
    def test_actual_export_adapter_and_clock_ownership_elaboration(self):
        path=Path(__file__).resolve().parents[2]/'evidence/genesys-master-aux-gray-link-2026-11-07/ps-hpm-wrapper-v2/pins.tsv'
        ps=SimpleNamespace(inputs={},outputs={})
        for line in path.read_text().splitlines():
            name,direction,left,right=line.split('\t')
            width=abs(int(left)-int(right))+1 if left and right else 1
            (ps.inputs if direction=='I' else ps.outputs)[name]=Signal(width)
        codec=Raw20Codec()
        top=GenesysMasterIntegration(ps,codec.channel,Signal(),Signal())
        top.submodules.codec=codec
        self.assertEqual(top.csr.registers['profile_identity']['address'],0xa0000800)
        self.assertEqual(top.csr.registers['aux_aux_tx_length']['address'],0xa0002000)
        self.assertEqual(top.ingress.management.BASE,0xb0000000)
        fragment=top.get_fragment()
        names={cd.name for cd in fragment.clock_domains}
        self.assertTrue({'management','control','ps','sys','rtio_rx','rio','rio_phy'}<=names)
        self.assertFalse(set(fragment.sync)-names)
        self.assertTrue(all(cd.rst is not None for cd in fragment.clock_domains))
        self.assertIs(top.aux.link_layer,top.master.link_layer)

if __name__=='__main__':unittest.main()
