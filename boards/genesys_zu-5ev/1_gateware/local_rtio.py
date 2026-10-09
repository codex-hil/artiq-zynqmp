"""Local upstream RTIO behind a PS AXI master, without a LiteX SoC migration.

Uses LiteX only for its maintained AXI bridge and MiSoC for ARTIQ's CSR ABI.
Optional upstream DMA uses PS HP0 DDR; the optional BRAM analyzer reuses
ARTIQ MessageEncoder. DRTIO remains separate.
"""
import json
from pathlib import Path

from migen import Module, Signal
from misoc.interconnect import csr_bus, wishbone2csr
from litex.soc.interconnect.axi import AXIInterface, AXI2Wishbone
from litex.soc.interconnect import wishbone
from artiq.gateware import rtio
from artiq.gateware.rtio.phy import ttl_simple

CSR_BASE = 0xA0000000
BANKS = {"rtio": 0, "rtio_core": 1, "rtio_moninj": 2}


class LocalRTIO(Module):
    def __init__(self, output_pad, input_pad, dma_bus=None, analyzer=False):
        self.submodules.ttl_out = ttl_simple.Output(output_pad)
        self.submodules.ttl_in = ttl_simple.Input(input_pad)
        self.ttl_in.probes = [self.ttl_in.input_state]
        channels = [rtio.Channel.from_phy(self.ttl_out), rtio.Channel.from_phy(self.ttl_in)]
        self.submodules.rtio_tsc = rtio.TSC(glbl_fine_ts_width=0)
        self.submodules.rtio_core = rtio.Core(self.rtio_tsc, channels)
        self.submodules.rtio = rtio.KernelInitiator(self.rtio_tsc, now64=True)
        if dma_bus is None:
            self.comb += self.rtio.cri.connect(self.rtio_core.cri)
        else:
            from zynqmp_dma import DMA
            from artiq.gateware.rtio.cri import CRISwitch
            self.submodules.rtio_dma = DMA(dma_bus)
            self.submodules.cri_con = CRISwitch(
                [self.rtio.cri, self.rtio_dma.cri], self.rtio_core.cri)
        self.submodules.rtio_moninj = rtio.MonInj(channels)
        if analyzer:
            from analyzer_bram import AnalyzerBRAM
            self.submodules.rtio_analyzer = AnalyzerBRAM(self.rtio_tsc, self.rtio_core.cri)

        # ZynqMP MAXIGP exports a 40-bit physical address, even with a
        # 32-bit data bus. Confirmed against Piotr's archived XSA/HWH.
        self.axi = AXIInterface(data_width=32, address_width=40, id_width=16)
        self.submodules.wb2csr = wishbone2csr.WB2CSR(
            bus_wishbone=wishbone.Interface(data_width=32, address_width=40, addressing="word"),
            bus_csr=csr_bus.Interface(data_width=32, address_width=14)
        )
        self.submodules.axi2wb = AXI2Wishbone(
            self.axi, self.wb2csr.wishbone, base_address=CSR_BASE
        )
        self.submodules.banks = csr_bus.CSRBankArray(
            self, lambda name, memory: dict(BANKS, rtio_dma=3, cri_con=4, rtio_analyzer=5).get(name) if memory is None else None,
            data_width=32, address_width=14
        )
        self.submodules.csr_interconnect = csr_bus.Interconnect(
            self.wb2csr.csr, self.banks.get_buses()
        )

    def write_map(self, destination):
        """Use finalized CSR sizes/order; never duplicate offsets in firmware."""
        registers = {}
        for name, csrs, bank_id, bank in self.banks.banks:
            offset = CSR_BASE + bank_id * 0x800
            for register in csrs:
                words = (register.size + 31) // 32
                registers[name + "_" + register.name] = {
                    "address": offset, "words": words, "bits": register.size,
                    "word_order": "big", "word_bytes": 4,
                }
                offset += words * 4
        Path(destination).write_text(json.dumps({
            "kind": "gateware-map-not-hardware-evidence",
            "csr_base": CSR_BASE, "csr_data_width": 32,
            "channels": {"ttl_out": 0, "ttl_in": 1},
            "fine_ts_width": 0, "registers": registers,
        }, indent=2) + "\n")


def connect_ps_hpm0(module, ps, axi):
    """Wire Piotr's exported PS pins, validating every mandatory port width."""
    module.comb += ps.inputs["maxihpm0_fpd_aclk"].eq(module.cd_sys.clk)
    for channel, fields in {
        "aw": "id addr len size burst lock cache prot qos valid ready",
        "ar": "id addr len size burst lock cache prot qos valid ready",
        "w": "data strb last valid ready",
        "b": "id resp valid ready",
        "r": "id data resp last valid ready",
    }.items():
        for field in fields.split():
            name = "maxigp0_" + channel + field
            signal = getattr(getattr(axi, channel), field)
            collection = ps.inputs if name in ps.inputs else ps.outputs
            if name not in collection:
                raise ValueError("Missing PS port: " + name)
            pin = collection[name]
            if len(pin) != len(signal):
                raise ValueError(f"PS port width mismatch: {name}: {len(pin)} != {len(signal)}")
            if collection is ps.inputs:
                module.comb += pin.eq(signal)
            else:
                module.comb += signal.eq(pin)
