"""Asynchronous MAC memory: registered read data, wraparound/backpressure."""
import env
import pytest
from migen import *
from migen.fhdl.specials import READ_FIRST
from migen.genlib.fifo import AsyncFIFO

@pytest.mark.parametrize('periods',[(6,10),(10,6)])
def test_registered_read_fifo(periods):
 m=Module();m.submodules.fifo=f=AsyncFIFO(12,32)
 count=Signal(12)
 m.comb += f.din.eq(count)
 m.sync.write += If(f.we & f.writable,count.eq(count+1))
 fragment=m.get_fragment()
 memories=[s for s in fragment.specials if isinstance(s,Memory)]
 assert len(memories)==1
 for port in memories[0].ports:
  if port.dat_r is not None:port.mode=READ_FIRST
  else:
   # Migen MemoryToArray predates write-only ports; unused dummy read output
   # is simulation-only and does not modify the generated target.
   port.dat_r=Signal(12)
 @passive
 def write():
  for cycle in range(20000):
   yield f.we.eq(cycle%7 not in (1,2));yield
 def read():
  expected=0
  for cycle in range(10000):
   yield f.re.eq(cycle%11 not in (3,4,5,6))
   if (yield f.readable) and (yield f.re):
    assert (yield f.dout)==expected
    expected+=1
    if expected==1000:return
   yield
  raise AssertionError('FIFO stalled')
 run_simulation(fragment,{'write':write(),'read':read()},clocks=dict(zip(['write','read'],periods)))
