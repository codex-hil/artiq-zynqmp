"""DMA ownership and abort reach actual AUX/SED target; LGPL-3.0-or-later.

Functional reset simulation; no physical CDC/timing qualification.
"""
import unittest
from migen import Module, Signal, Mux
from migen.sim import run_simulation
from migen.genlib.resetsync import AsyncResetSynchronizer
from artiq.gateware.rtio.cri import Interface
from aux_ps import AuxPS
from test_aux_ps import FunctionalReset

class DMATransportTests(unittest.TestCase):
    def test_owner_and_abort_cancel_future_event_preserve_phy_and_tsc(self):
        d=Module();pad=Signal();owner=Signal();abort=Signal();cri=Interface()
        d.submodules.ps=p=AuxPS(output_pad=pad,dma_cri=cri,
            dma_owner=owner,dma_rtio_reset=abort)
        b=p.satellite.backend
        trigger=Signal();previous_trigger=Signal()
        # Emit one native RX-clock CRI command. Python stimulus does not drive
        # an edge-width pulse across aliased simulator clock domains.
        d.sync.aux_rx += [previous_trigger.eq(trigger),
            cri.cmd.eq(Mux(trigger != previous_trigger,1,0))]
        def run():
            yield p.reset.eq(0)
            yield p.rtio_reset_request.storage_full.eq(0)
            yield p.phy_reset_request.storage_full.eq(0)
            yield owner.eq(1)
            for _ in range(25):yield
            self.assertEqual((yield b.cri_switch.selected.storage),1)
            self.assertEqual((yield b.rtio_reset),0)
            self.assertEqual((yield b.phy_reset),0)
            start=(yield b.tsc.coarse_ts)
            # First transition executes; second is admitted then cancelled.
            for timestamp,value in ((start+1200,1),(start+2000,0)):
                yield cri.chan_sel.eq(0);yield cri.o_address.eq(0)
                yield cri.o_timestamp.eq(timestamp<<3);yield cri.o_data.eq(value)
                yield trigger.eq(~(yield trigger))
                for _ in range(8):yield
            while (yield b.tsc.coarse_ts)<start+1300:yield
            self.assertEqual((yield b.async_errors.raw_bits()),0)
            self.assertEqual((yield pad),1)
            yield abort.eq(1)
            for _ in range(10):yield
            self.assertEqual((yield b.reset_applied),1)
            yield abort.eq(0)
            previous=(yield b.tsc.coarse_ts)
            for _ in range(900):
                yield
                now=(yield b.tsc.coarse_ts)
                self.assertEqual(now,previous+1);previous=now
                self.assertEqual((yield pad),1)
            # Queue reset did not park the switch or prevent a new command.
            yield cri.o_timestamp.eq((previous+1200)<<3);yield cri.o_data.eq(0)
            yield trigger.eq(~(yield trigger))
            for _ in range(1250):yield
            self.assertEqual((yield pad),0)
            yield owner.eq(0);yield;yield
            self.assertEqual((yield b.cri_switch.selected.storage),0)
        run_simulation(d,{'gth_rx':run()},
            clocks={'sys':10,'gth_tx':8,'gth_rx':8,'aux_sys':10,'aux_tx':8,'aux_rx':8},
            special_overrides={AsyncResetSynchronizer:FunctionalReset})

    def test_incomplete_dma_connection_rejected(self):
        with self.assertRaisesRegex(ValueError,'DMA requires'):
            AuxPS(dma_cri=Interface())

if __name__=='__main__':unittest.main()
