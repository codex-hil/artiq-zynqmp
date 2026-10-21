"""Negative control: the hardware zero-payload bug must fail the transport test."""
import importlib
import sys
from pathlib import Path
from migen import Cat
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gateware'))
cls=importlib.import_module('generate-link').DualLink
original=cls.drive_payload
def broken(self, amplitude, parent):
 for core in self.cores:
  parent.comb += [core.sink.converter0.eq(Cat(amplitude,amplitude)),core.sink.converter1.eq(0)]
try:
 cls.drive_payload=broken
 try:importlib.import_module('test_mode3').test_payload_reaches_both_transport_inputs()
 except AssertionError:print('PASS: old zero-payload wiring rejected')
 else:raise SystemExit('FAIL: regression test accepted the broken wiring')
finally:cls.drive_payload=original
