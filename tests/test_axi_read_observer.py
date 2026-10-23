"""Passive observer handshake and reset-history controls; LGPL-3.0-or-later."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/ddr'))
from axi_read_observer import AXIReadObserver
from migen import Module,run_simulation
from litex.soc.interconnect.axi import AXIInterface

class TB(Module):
 def __init__(self):
  self.bus=AXIInterface(data_width=64,address_width=49,id_width=6)
  self.submodules.observer=AXIReadObserver(self.bus,2)

class Tests(unittest.TestCase):
 def test_handshakes_stalls_and_no_epoch_no_quiet(self):
  tb=TB();b=tb.bus;o=tb.observer
  def run():
   yield;self.assertEqual((yield o.quiet),0)
   yield o.epoch_qualified.eq(1);yield;yield
   self.assertEqual((yield o.quiet),1)
   yield b.ar.valid.eq(1);yield;yield
   self.assertEqual((yield o.outstanding),0);self.assertEqual((yield o.quiet),0)
   yield b.ar.ready.eq(1);yield;yield b.ar.valid.eq(0);yield
   self.assertEqual((yield o.outstanding),1)
   yield b.r.valid.eq(1);yield b.r.last.eq(1);yield;yield
   self.assertEqual((yield o.outstanding),1)
   yield b.r.ready.eq(1);yield;yield b.r.valid.eq(0);yield
   self.assertEqual((yield o.outstanding),0);self.assertEqual((yield o.quiet),1)
  run_simulation(tb,run())
 def test_overflow_unmatched_reply_and_response_error_sticky(self):
  for fault in ['overflow','unmatched','response']:
   tb=TB();b=tb.bus;o=tb.observer
   def run():
    yield o.epoch_qualified.eq(1)
    if fault=='overflow':
     yield b.ar.valid.eq(1);yield b.ar.ready.eq(1)
     for _ in range(5):yield
     yield b.ar.valid.eq(0)
    else:
     yield b.r.valid.eq(1);yield b.r.ready.eq(1)
     yield b.r.last.eq(fault=='unmatched');yield b.r.resp.eq(2 if fault=='response' else 0)
     yield;yield;yield b.r.valid.eq(0)
    yield;yield
    self.assertEqual((yield o.quiet),0)
    self.assertEqual((yield o.response_error) if fault=='response' else (yield o.accounting_error),1)
   run_simulation(tb,run())
 def test_fresh_reset_state_does_not_certify_external_drain(self):
  # Independent bus history is unknowable to a newly reset monitor.
  tb=TB()
  def run():
   yield;yield
   self.assertEqual((yield tb.observer.outstanding),0)
   self.assertEqual((yield tb.observer.quiet),0)
  run_simulation(tb,run())
if __name__=='__main__':unittest.main()
