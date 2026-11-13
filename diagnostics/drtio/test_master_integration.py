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
        top=GenesysMasterIntegration(ps,codec.channel,Signal(),Signal(),codec=codec,
            link_status=SimpleNamespace(reset_done=Signal(),clock_active=Signal(),aligned=Signal()))
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
        self.assertIs(top.gt_reset_request,top.ingress.coordinator.reset)

    def exercise_two_hpm_roundtrip(self,guarded=False,xilinx=False,not_ready_link=False):
        from migen import ClockDomain,ClockSignal
        from migen.sim import run_simulation
        from migen.genlib.resetsync import AsyncResetSynchronizer
        from test_master_ps_cdc import FunctionalReset
        from test_master_csr import AXIMaster
        path=Path(__file__).resolve().parents[2]/'evidence/genesys-master-aux-gray-link-2026-11-07/ps-hpm-wrapper-v2/pins.tsv'
        ps=SimpleNamespace(inputs={},outputs={})
        for line in path.read_text().splitlines():
            name,direction,left,right=line.split('\t')
            width=abs(int(left)-int(right))+1 if left and right else 1
            (ps.inputs if direction=='I' else ps.outputs)[name]=Signal(width)
        codec=Raw20Codec()
        options={}
        if not_ready_link:
            options=dict(codec=codec,link_status=SimpleNamespace(reset_done=Signal(),clock_active=Signal(),aligned=Signal()))
        top=GenesysMasterIntegration(ps,codec.channel,ClockSignal('tx_source'),ClockSignal('rx_source'),guarded_candidate=guarded,**options)
        top.submodules.codec=codec
        for name in ('pl_source','tx_source','rx_source'):
            setattr(top.clock_domains,'cd_'+name,ClockDomain(name,reset_less=True))
        top.comb+=ps.outputs['pl_clk0'].eq(ClockSignal('pl_source'))
        def host(index):
            bus=SimpleNamespace()
            for channel,names in {'aw':'id addr len size burst lock cache prot qos valid ready',
                'ar':'id addr len size burst lock cache prot qos valid ready',
                'w':'data strb last valid ready','b':'id resp valid ready',
                'r':'id data resp last valid ready'}.items():
                fields={}
                for field in names.split():
                    name=f'maxigp{index}_'+channel+field
                    fields[field]=(ps.inputs if name in ps.inputs else ps.outputs)[name]
                setattr(bus,channel,SimpleNamespace(**fields))
            return AXIMaster(bus)
        management,target=host(1),host(0)
        base=0xb0000000;length=0xa0002000
        state={'open':0,'done':0}
        def poll(mask,value):
            for _ in range(100):
                status=yield from management.read(base+8)
                if status&mask==value:return
            self.fail('Adapter management status timeout')
        def reopen():
            yield from management.write(base+4,0)
            yield from poll(3,3)
            yield from management.write(base+4,2)
            yield from poll(5,4)
        def manager():
            yield ps.outputs['pl_resetn0'].eq(1)
            for _ in range(24):yield
            self.assertEqual((yield from management.read(base)),0x47524d31)
            yield from reopen()
            state['open']=1
            for _ in range(3000):
                if state['done']==1:break
                yield
            else:self.fail('Initial HPM0 target stalled')
            yield from management.write(base+4,1)
            yield from poll(5,1)
            self.assertEqual((yield from management.read(base)),0x47524d31)
            self.assertEqual((yield ps.inputs['maxigp0_arready']),0)
            self.assertEqual((yield ps.inputs['maxigp0_awready']),0)
            yield from reopen()
            state['open']=2
            for _ in range(3000):
                if state['done']==2:return
                yield
            self.fail('HPM0 did not recover')
        def requester():
            for episode in (1,2):
                for _ in range(3000):
                    if state['open']==episode:break
                    yield
                else:self.fail('No target admission')
                if not_ready_link:self.assertEqual((yield codec.channel.rx_ready),0)
                self.assertEqual((yield from target.read(0xa0000800)),0x47534d31)
                self.assertEqual((yield from target.read(length)),0)
                value=12 if episode==1 else 68
                yield from target.write(length,value)
                self.assertEqual((yield from target.read(length)),value)
                state['done']=episode
        clocks={'pl_source':8,'tx_source':14,'rx_source':18,
                'management':8,'control':8,'ps':8,'sys':14,'rio':14,'rio_phy':14,'rtio_rx':18}
        for name in ('ps','sys','rtio_rx','rio','rio_phy'):
            clocks['aux_release_'+name]=clocks[name]
        for name,crossing in top.csr.ps_cdc.crossings.items():
            periods=(14,8) if name in ('b','r') else (8,14)
            for domain,period in zip(crossing._fragment.clock_domains,periods):clocks[domain.name]=period
        overrides={AsyncResetSynchronizer:FunctionalReset}
        if xilinx:
            from migen.genlib.cdc import MultiReg
            from migen.build.xilinx.common import XilinxMultiReg
            overrides[MultiReg]=XilinxMultiReg
        run_simulation(top,{'management':manager(),'ps':requester()},clocks,
                       special_overrides=overrides)
        self.assertEqual(state['done'],2)

    def test_two_hpm_signal_adapters_and_reset_roundtrip(self):self.exercise_two_hpm_roundtrip()
    def test_guarded_two_hpm_signal_adapters_and_reset_roundtrip(self):self.exercise_two_hpm_roundtrip(True)

    def test_guarded_hpm_roundtrip_exact_xilinx_multireg(self):self.exercise_two_hpm_roundtrip(True,True)

if __name__=='__main__':unittest.main()
