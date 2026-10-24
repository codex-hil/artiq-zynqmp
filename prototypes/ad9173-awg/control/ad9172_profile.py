"""Transport-independent AD9172 profile. Rechecked against AD9172 Rev.C
Tables53,54,55,56,57 and register map; derived from preserved AD9173 reference.
No imports of hardware sessions, USB, JTAG, cable IDs, or programming routines.
This is a warm-clock profile: HMC VCO/DAC clock startup is a separate prerequisite.
HMC reads over the FMC unidirectional SPI path are NOT assumed possible.
"""
from typing import Protocol

FS = 4_915_200_000
class SPI(Protocol):
    def read_dac(self, address: int) -> int: ...
    def write_dac(self, address: int, value: int) -> None: ...
    def write_hmc(self, address: int, value: int) -> None: ...
    def wait_ms(self, duration: int) -> None: ...

class ProfileError(RuntimeError):
    pass

def identify(spi: SPI):
    identity = tuple(spi.read_dac(a) for a in (4, 5))
    if identity != (0x72, 0x91):
        raise ProfileError(f'AD9172 identity mismatch: {identity!r}')
    return identity

def clock_status(spi: SPI):
    return {a: spi.read_dac(a) for a in (0x7b5, 0xc3, 0x281)}

def require_lock(spi: SPI, address: int, name: str):
    if not spi.read_dac(address) & 1:
        raise ProfileError(f'{name} is not locked')

def write_pairs(spi: SPI, pairs):
    for address, value in pairs:
        spi.write_dac(address, value)

def configure_links(spi: SPI):
    """Mode3 / dual L2 / 6.144 Gb/s; caller keeps FPGA samples muted.
    Does not initialize HMC PLLs or the DAC PLL from a cold board.
    """
    identify(spi)
    require_lock(spi, 0x7b5, 'DAC PLL')
    require_lock(spi, 0xc3, 'DAC DLL')
    if spi.read_dac(0x799) & 63 != 5:
        raise ProfileError('DAC clock divider does not match 4.9152 GS/s profile')
    write_pairs(spi, [(8, 0xc0), (0x596, 4), (0x3f, 0x30), (0x90, 0),
        (0x100, 0), (0x300, 8), (0x110, 0x23), (0x111, 0x82),
        (0x084, 1), (0x312, 0x10)])
    if spi.read_dac(0x110) != 0x23 or spi.read_dac(0x111) != 0x82:
        raise ProfileError('Mode readback failed')
    for link in range(2):
        write_pairs(spi, [(0x300, 8 | link << 2), (0x475, 9),
            (0x450, 0x61), (0x451, link), (0x452, 0), (0x453, 0x81),
            (0x454, 1), (0x455, 31), (0x456, 1), (0x457, 15),
            (0x458, 15), (0x459, 0x20), (0x45b, 0), (0x45c, 0),
            (0x45d, 0xa4 + link), (0x476, 0x14), (0x480, 0x38),
            (0x481, 0x38), (0x475, 1)])
    write_pairs(spi, [(0x240, 0xaa), (0x241, 0xaa), (0x242, 0x55), (0x243, 0x55)]
        + [(a, 0x1f) for a in range(0x244, 0x24c)]
        + [(0x201, 0x0f), (0x203, 0), (0x253, 1), (0x254, 1),
           (0x210, 0x16), (0x216, 5), (0x212, 255), (0x212, 0),
           (0x210, 0x87), (0x216, 0x11), (0x213, 1), (0x213, 0), (0x200, 0)])
    spi.wait_ms(100)
    for a, b in [(0x86, 0x40), (0x86, 0), (0x87, 1)]:
        write_pairs(spi, [(0x210, a), (0x216, b), (0x213, 1), (0x213, 0)])
    write_pairs(spi, [(0x280, 5), (0x280, 1)])
    spi.wait_ms(200)
    require_lock(spi, 0x281, 'SERDES PLL')
    write_pairs(spi, [(0x308, 0x37), (0x309, 0x13), (0x30a, 0x25),
        (0x30b, 1), (0x334, 0), (0x3b, 0xf1), (0x3a, 2), (0x300, 11)])
    spi.wait_ms(500)

def link_status(spi: SPI):
    previous = spi.read_dac(0x300)
    result = []
    try:
        for link in range(2):
            spi.write_dac(0x300, (previous & ~4) | (link << 2))
            status = {a: spi.read_dac(a) for a in
                      (0x470, 0x471, 0x472, 0x473, 0x46d, 0x46e, 0x46f)}
            result.append(status)
    finally:
        spi.write_dac(0x300, previous)
    return result

def require_links(spi: SPI):
    status = link_status(spi)
    if not all(all(s[a] & 3 == 3 for a in range(0x470, 0x474)) and
               all(s[a] & 3 == 0 for a in range(0x46d, 0x470)) for s in status):
        raise ProfileError('CGS/ILAS/data status incomplete or error flags set')
    return status

def nco_word(frequency_hz: int):
    if not 0 <= frequency_hz < FS // 2:
        raise ValueError('Frequency outside first Nyquist zone')
    return (frequency_hz * (1 << 48) + FS // 2) // FS

def set_tones(spi: SPI, frequencies=(149_000_000, 151_000_000)):
    """Program while caller holds FPGA payload at zero; never unmutes RF."""
    if len(frequencies) != 2:
        raise ValueError('Two DAC frequencies required')
    words = [nco_word(f) for f in frequencies]
    identify(spi)
    require_links(spi)
    previous = spi.read_dac(8)
    try:
        for page, ftw in zip((0x40, 0x80), words):
            write_pairs(spi, [(8, page), (0x113, 0)] +
                        [(0x114+i, (ftw >> (8*i)) & 255) for i in range(6)] + [(0x113, 1)])
            spi.wait_ms(10)
            actual = sum(spi.read_dac(0x114+i) << (8*i) for i in range(6))
            if actual != ftw or not spi.read_dac(0x113) & 2:
                raise ProfileError('NCO load/readback failed; keep payload muted')
    finally:
        spi.write_dac(8, previous)
    return words

def prepare_fpga_dsp(spi: SPI):
    """Select streamed I/Q, zero channel shift, main-NCO complex interpolation.
    Leaves TXEN digitally muted (0x596=4); caller validates before enabling RF.
    """
    identify(spi)
    previous = spi.read_dac(8)
    try:
        write_pairs(spi, [(8, 9), (0x146, 0), (0x147, 8), (0x130, 0x40),
                         (0x131, 0)] + [(a, 0) for a in range(0x132, 0x138)] +
                        [(0x131, 1), (8, 0xc0), (0x1e6, 0), (0x112, 8),
                         (0x90, 0), (0x596, 4)])
        for page in (1, 8):
            spi.write_dac(8, page)
            if spi.read_dac(0x130) != 0x40 or not spi.read_dac(0x131) & 2 or any(
                    spi.read_dac(a) for a in range(0x132, 0x138)):
                raise ProfileError('Channel DSP readback failed; keep RF muted')
    finally:
        spi.write_dac(8, previous)
