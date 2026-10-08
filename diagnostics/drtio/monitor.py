"""Clock/event counters crossing into independent PS management clock."""
from migen import Module, Signal, Cat, If, ClockDomainsRenamer
from migen.genlib.cdc import MultiReg
from misoc.interconnect.csr import AutoCSR, CSR, CSRStorage, CSRStatus


class GrayCounter(Module):
    def __init__(self, domain, width=32):
        self.enable = Signal(reset=1)
        self.value = Signal(width)
        binary = Signal(width)
        next_value = Signal(width)
        gray = Signal(width, name=domain + '_gray_source')
        gray.attr.add('keep')
        synced = Signal(width, name=domain + '_gray_sync')
        self.comb += next_value.eq(binary + 1)
        getattr(self.sync, domain).__iadd__(If(self.enable,
            binary.eq(next_value), gray.eq(next_value ^ (next_value >> 1))))
        self.specials += MultiReg(gray, synced, odomain='sys')
        # Gray -> binary; each bit is xor of the Gray prefix above it.
        for i in range(width):
            value = synced[width-1]
            for j in range(width-2, i-1, -1):
                value = value ^ synced[j]
            self.comb += self.value[i].eq(value)


class Monitor(Module, AutoCSR):
    def __init__(self, status, rx_error):
        self.magic = CSRStatus(32, name='magic')
        self.reset = CSRStorage(1, reset=1, name='reset')
        self.tx_enable = CSRStorage(1, name='tx_enable')
        self.loopback = CSRStorage(3, reset=2, name='loopback') # near-end PMA
        self.prbs = CSRStorage(4, reset=1, name='prbs') # RX PRBS7
        self.tx_prbs = CSRStorage(4, reset=1, name='tx_prbs') # independent negative control
        self.snapshot = CSR(name='snapshot')
        self.status = CSRStatus(len(status), name='status')
        self.boot_ticks = CSRStatus(32, name='boot_ticks')
        self.rx_ticks = CSRStatus(32, name='rx_ticks')
        self.tx_ticks = CSRStatus(32, name='tx_ticks')
        self.prbs_errors = CSRStatus(32, name='prbs_errors')
        status_sync = Signal(len(status))
        self.specials += MultiReg(status, status_sync)
        self.comb += self.magic.status.eq(0x44525430)
        boot_count = Signal(32)
        self.sync += boot_count.eq(boot_count + 1)
        self.submodules.rx_count = GrayCounter('gth_rx')
        self.submodules.tx_count = GrayCounter('gth_tx')
        self.submodules.error_count = GrayCounter('gth_rx')
        self.comb += self.error_count.enable.eq(rx_error)
        self.sync += If(self.snapshot.re,
            self.status.status.eq(status_sync),
            self.boot_ticks.status.eq(boot_count),
            self.rx_ticks.status.eq(self.rx_count.value),
            self.tx_ticks.status.eq(self.tx_count.value),
            self.prbs_errors.status.eq(self.error_count.value))
