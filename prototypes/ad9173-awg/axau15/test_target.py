import importlib.util
from pathlib import Path
import sys
from migen import *
from migen.genlib.cdc import BusSynchronizer
from migen.sim import run_simulation
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'gateware'))
sys.path.insert(0, str(ROOT / 'control'))
from ad9173_profile import identify, configure_links, hmc_reference, set_tones, nco_word, ProfileError, prepare_fpga_dsp
from importlib import import_module
DualLink = import_module('generate-link').DualLink

class FakeSPI:
    def __init__(self):
        self.regs = {4: 0x73, 5: 0x91, 0x7b5: 1, 0xc3: 1, 0x281: 1, 0x799: 5,
                     8: 0, 0x300: 11, **{a: 3 for a in range(0x470, 0x474)}}
        self.writes = []
    def read_dac(self, a):
        return self.regs.get(a, 0)
    def write_dac(self, a, v):
        self.writes.append(('dac', a, v))
        self.regs[a] = 3 if a in (0x113, 0x131) and v == 1 else v
    def write_hmc(self, a, v):
        self.writes.append(('hmc', a, v))
    def wait_ms(self, ms):
        pass

def test_identity_and_clock_failure_precede_configuration_writes():
    import pytest
    for address, value in [(4, 0), (5, 0), (0x7b5, 0), (0xc3, 0), (0x799, 4)]:
        spi = FakeSPI()
        spi.regs[address] = value
        with pytest.raises(ProfileError):
            configure_links(spi)
        assert not spi.writes

def test_reference_output_is_explicit_and_separate():
    import pytest
    spi = FakeSPI()
    with pytest.raises(ProfileError):
        hmc_reference(spi, output=12, routing_confirmed=False, driver_mode=0x10)
    assert not spi.writes
    hmc_reference(spi, output=12, routing_confirmed=True, driver_mode=0x10)
    assert ('hmc', 0x141, 12) in spi.writes
    assert not any(a == 0x14a for _, a, _ in spi.writes)

def test_nco_frequency_quantization_and_link_guard():
    import pytest
    spi = FakeSPI()
    for f in (149_000_000, 151_000_000):
        assert abs(nco_word(f) * 4_915_200_000 / 2**48 - f) < 0.00001
    spi.regs[0x471] = 1
    with pytest.raises(ProfileError):
        set_tones(spi)
    assert not any(0x114 <= a <= 0x119 for _, a, _ in spi.writes)
    spi.regs[0x471] = 3
    assert set_tones(spi) == [nco_word(149_000_000), nco_word(151_000_000)]
    assert spi.regs[8] == 0

def test_signed_payload_coherent_cdc_and_recovery():
    class DUT(Module):
        def __init__(self):
            for name in ['sys', 'jesd'] + [f'jesd_phy{i}_tx' for i in range(4)]:
                setattr(self.clock_domains, 'cd_' + name, ClockDomain(name))
            self.submodules.link = DualLink(subclass=0, hd=1, did=0x61)
            self.submodules.cdc = BusSynchronizer(16, 'sys', 'jesd')
            self.link.drive_payload(self.cdc.o, self)
    dut = DUT()
    def stimulus():
        # Full, half, zero, asymmetric, negative fullscale, recovery.
        for word in (0x7fff, 0x4000, 0, 0x1234, 0x8000, 0xffff, 0x7fff):
            yield dut.cdc.i.eq(word)
            for _ in range(100):
                yield
            for inputs in dut.link.converter_inputs:
                assert (yield inputs[0]) == word | word << 16
                assert (yield inputs[1]) == 0
    run_simulation(dut, stimulus(), clocks={'sys': 10, 'jesd': 6, **{f'jesd_phy{i}_tx': 6 for i in range(4)}})

def test_generated_dedicated_ref_and_sample_sign(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    spec = importlib.util.spec_from_file_location('axau15_generator', ROOT / 'axau15/generate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from migen.fhdl import verilog
    from litex.build.xilinx.common import xilinx_special_overrides
    dut = module.AXAU15()
    assert dut.pll_config['linerate'] == 6_144_000_000
    text = str(verilog.convert(dut, ios=dut.ios, name='axau15_awg',
                              special_overrides=xilinx_special_overrides))
    assert 'IBUFDS_GTE4' in text
    assert '.GTGREFCLK0(1\'d0)' in text and '.GTGREFCLK1(1\'d0)' in text
    assert text.count('.TXPRBSSEL(3\'d0)') == 4 or text.count('.TXPRBSSEL(1\'d0)') == 4
    assert 'input spi_en' in text


def test_streamed_dsp_keeps_rf_muted():
    spi = FakeSPI()
    prepare_fpga_dsp(spi)
    assert spi.regs[0x130] == 0x40  # internal DC injection off
    assert spi.regs[0x1e6] == 0
    assert spi.regs[0x112] == 8
    assert spi.regs[0x596] == 4
    assert spi.regs[8] == 0
