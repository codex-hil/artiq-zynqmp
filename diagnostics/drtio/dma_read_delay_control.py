"""Separate opt-in delayed DMA diagnostic peripheral; LGPL-3.0-or-later.

Not used by diag_gateware or the qualified hardware profile. Fixed delay is
compiled in; the host can arm once, never write an unbounded delay. No reset
is permitted while reads are outstanding, including diagnostic reset.
"""
import json,hashlib
from decimal import Decimal
from pathlib import Path
from migen import Module, Signal, If
from misoc.interconnect.csr import CSR, CSRStatus
from litex.soc.interconnect.axi import AXIInterface
from dma_csr import DMACSR
from dma_read_delay import DMAReadDelay


def delay_cycles(sys_clk_hz, delay_us=2000):
    if not isinstance(sys_clk_hz, int) or sys_clk_hz <= 0:
        raise ValueError('Positive integer sys clock frequency required')
    if not isinstance(delay_us, int) or delay_us <= 1000:
        raise ValueError('Delay must exceed the firmware 1ms admission lead')
    cycles=(sys_clk_hz*delay_us+999999)//1000000
    if not 1 <= cycles <= 1048576:
        raise ValueError('Delay exceeds bounded read gate capacity')
    return cycles


def verify_ps_clock(ip_paths, expected_hz):
    """Require one imported JSON PS IP with the explicit PL0 frequency."""
    matches=[]
    for name in ip_paths:
        path=Path(name)
        if path.suffix!='.xci':continue
        data=json.loads(path.read_text())
        params=data.get('ip_inst',{}).get('parameters',{}).get('component_parameters',{})
        value=params.get('PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ')
        if value is not None:
            hz=Decimal(value[0]['value'])*1000000
            if hz!=expected_hz:raise ValueError('Requested delay clock differs from imported PS PL0')
            matches.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                configured_hz=int(hz),physical_measurement='NOT_RUN'))
    if len(matches)!=1:raise ValueError('Exactly one explicit imported PS PL0 clock required')
    return matches[0]


class ReadDelayControl(Module):
    def __init__(self, gate, launch, idle, watchdog, cycles):
        self.arm=CSR(1,name='dma_lab_delay_arm')
        self.armed=CSRStatus(1,name='dma_lab_delay_armed')
        self.holding=CSRStatus(1,name='dma_lab_delay_holding')
        self.arm_rejected=CSRStatus(32,name='dma_lab_delay_arm_rejected')
        self.triggers=CSRStatus(32,name='dma_lab_delay_triggers')
        self.rejected=CSRStatus(32,name='dma_lab_delay_rejected')
        self.cycles=CSRStatus(32,reset=cycles,name='dma_lab_delay_cycles')
        self.csrs=[self.arm,self.armed,self.holding,self.arm_rejected,
                   self.triggers,self.rejected,self.cycles]
        attempt=Signal();fire=Signal();safe=Signal()
        # Keep at least half the watchdog available for drain after release.
        self.comb += [attempt.eq(self.arm.re & self.arm.r),
                      fire.eq(self.armed.status & launch),safe.eq(watchdog > 2*cycles),
                      gate.trigger.eq(fire & safe),gate.idle.eq(idle),
                      self.holding.status.eq(gate.holding)]
        self.sync += [
            If(attempt,
               If(idle & ~launch & ~gate.holding & ~self.armed.status,
                  self.armed.status.eq(1)).Else(
                  self.arm_rejected.status.eq(self.arm_rejected.status+1))),
            If(fire,self.armed.status.eq(0)),
            If(gate.accepted,self.triggers.status.eq(self.triggers.status+1)),
            If(gate.rejected | (fire & ~safe),self.rejected.status.eq(self.rejected.status+1))]


class LabDelayedDMACSR(DMACSR):
    def __init__(self, membus, *, sys_clk_hz, delay_us=2000, **kwargs):
        cycles=delay_cycles(sys_clk_hz,delay_us)
        internal=AXIInterface(data_width=len(membus.r.data),
                              address_width=len(membus.ar.addr),id_width=len(membus.ar.id))
        super().__init__(internal,**kwargs)
        self.submodules.read_delay=gate=DMAReadDelay(internal,membus,cycles)
        e=self.engine
        self.submodules.delay_control=control=ReadDelayControl(
            gate,e.start,~(e.active | e.recovering),self.watchdog.storage,cycles)
        self.csrs += control.csrs
        self.delay_config=dict(sys_clk_hz=sys_clk_hz,delay_us=delay_us,cycles=cycles,
                               watchdog_requirement='strictly greater than twice delay cycles',
                               scope='OPT_IN_LAB_NOT_HARDWARE_QUALIFIED')

    def memory_map(self,base):
        mapping=super().memory_map(base)
        mapping['laboratory_read_delay']=self.delay_config
        return mapping
