"""Bounded sys-domain CSR control for AsyncSatelliteDMA; LGPL-3.0-or-later.

No target/PS memory port is connected by this module. Fault must be explicitly
released. Host must acknowledge a latched result before starting another trace.
"""
from migen import Module,Signal,If,Cat,Mux
from misoc.interconnect.csr import CSR,CSRStorage,CSRStatus
from dma_async_engine import AsyncSatelliteDMA

class DMACSR(Module):
    def __init__(self,membus,arena_base=0x22000000,arena_size=0x200000):
        if arena_base<0 or arena_base%128 or arena_size<512 or arena_size%128:
            raise ValueError('Aligned arena of at least512 bytes required')
        if arena_base+arena_size > 1<<len(membus.ar.addr):
            raise ValueError('Arena exceeds memory address width')
        self.fault=Signal(reset=1)
        self.address=CSRStorage(len(membus.ar.addr),name='dma_address')
        self.time_offset=CSRStorage(64,name='dma_time_offset')
        self.max_bursts=CSRStorage(32,name='dma_max_bursts')
        self.watchdog=CSRStorage(32,reset=1<<24,name='dma_watchdog')
        self.start=CSR(1,name='dma_start');self.abort=CSR(1,name='dma_abort')
        self.clear=CSR(1,name='dma_clear')
        self.active=CSRStatus(1,name='dma_active');self.pending=CSRStatus(1,name='dma_pending')
        self.reject=CSRStatus(7,name='dma_reject')
        self.result_error=CSRStatus(8,name='dma_result_error')
        self.result_channel=CSRStatus(24,name='dma_result_channel')
        self.result_timestamp=CSRStatus(64,name='dma_result_timestamp')
        self.accepted=CSRStatus(32,name='dma_accepted')
        self.completed=CSRStatus(32,name='dma_completed')
        self.submodules.engine=e=AsyncSatelliteDMA(membus)
        self.cri=e.cri;self.rtio_reset_request=e.rtio_reset_request
        self.arena_base,self.arena_size=arena_base,arena_size
        self.csrs=[self.address,self.time_offset,self.max_bursts,self.watchdog,
            self.start,self.abort,self.clear,self.active,self.pending,self.reject,
            self.result_error,self.result_channel,self.result_timestamp,self.accepted,self.completed]
        attempt,launch,reason,expired=Signal(),Signal(),Signal(7),Signal()
        remaining=Signal(32);timed_out=Signal()
        invalid_window=(self.address.storage<arena_base) | (
            self.address.storage+(self.max_bursts.storage<<7)>arena_base+arena_size)
        bad_limit=(self.max_bursts.storage<4) | (self.max_bursts.storage>arena_size//128)
        self.comb += [attempt.eq(self.start.re & self.start.r),
            reason.eq(Cat(e.active,self.address.storage[:7]!=0,invalid_window,
                bad_limit,self.watchdog.storage==0,self.fault,self.pending.status)),
            launch.eq(attempt & (reason==0)),e.start.eq(launch),
            e.address.eq(self.address.storage),e.time_offset.eq(self.time_offset.storage),
            e.max_bursts.eq(self.max_bursts.storage),
            expired.eq(e.active & ~e.done & (remaining<=1)),
            # Readiness faults reject idle launches via reason. Only an active
            # epoch may propagate a fault into the RX SED abort/reset path;
            # otherwise no-TSC boot holds RTIO reset before AUX can get TSC.
            e.abort.eq((self.fault & e.active) | (self.abort.re & self.abort.r) | expired | (timed_out & e.active)),
            self.active.status.eq(e.active | launch)]
        self.sync += [If(launch,remaining.eq(self.watchdog.storage),timed_out.eq(0),
                self.accepted.status.eq(self.accepted.status+1)),
            If(e.active & (remaining!=0),remaining.eq(remaining-1)),
            If(expired,timed_out.eq(1)),
            If(attempt & (reason!=0),self.reject.status.eq(self.reject.status | reason)),
            If(self.clear.re & self.clear.r & ~e.active,
                self.pending.status.eq(0),self.reject.status.eq(0)),
            If(e.done,self.pending.status.eq(1),self.completed.status.eq(self.completed.status+1),
                self.result_error.status.eq(e.error | Mux(timed_out,32,0) | Mux(e.budget_error,64,0)),
                self.result_channel.status.eq(e.error_channel),self.result_timestamp.status.eq(e.error_timestamp))]

    def memory_map(self,base):
        address=base;regs={}
        for csr in self.csrs:
            words=(csr.size+31)//32
            regs[csr.name]={'address':address,'words':words,'bits':csr.size}
            address+=4*words
        return {'kind':'dma-csr-map-not-hardware','registers':regs,
            'arena':{'base':self.arena_base,'size':self.arena_size,'alignment':128},
            'limit_units':'128-byte AXI bursts; min4; zero rejected',
            'watchdog_units':'sys clocks; zero rejected',
            'result_protocol':'read latched result, write clear=1, then next start',
            'word_order':'MiSoC multiword CSRs: most significant word first'}
