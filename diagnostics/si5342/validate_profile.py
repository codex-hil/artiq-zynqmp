"""Check divider arithmetic and fractional enables before physical writes."""
from fractions import Fraction

def little(registers, address, width):
    return sum(registers[address+i] << (8*i) for i in range(width))

def validate(profile, factory):
    writes = {int(k,16):v for k,v in profile['writes'].items()}
    registers = {int(k,16):v for k,v in factory.items()}
    registers.update(writes)
    p = Fraction(little(registers,0x208,6),little(registers,0x20e,4))
    m = Fraction(little(registers,0x515,7),little(registers,0x51c,4))
    if p.denominator != 1 and not (writes[0x231]&0x10):
        raise ValueError('Fractional P divider disabled')
    if m.denominator != 1 and not (writes[0x521]&0x10):
        raise ValueError('Fractional M divider disabled')
    if (p.denominator!=1 and writes[0xb44]&1) or (m.denominator!=1 and writes[0xb44]&0x20):
        raise ValueError('P0/M fractional divider clocks disabled')
    if writes[0xb47] & 1 or writes[0xb48] & 1:
        raise ValueError('IN0 OOF clock disabled')
    vco = Fraction(profile['input_hz']) / p * m * 5
    xaxb = Fraction(little(registers,0x235,6),little(registers,0x23b,4))*48000000
    n = Fraction(little(registers,0x302,6),little(registers,0x308,4))
    if vco != profile['vco_hz'] or vco != xaxb:
        raise ValueError('Input and free-run VCO plans differ')
    if Fraction(profile['input_hz']) / p != Fraction(profile['pfd_hz']):
        raise ValueError('Unexpected phase detector frequency')
    for rbase,config in [(0x250,0x112),(0x253,0x117)]:
        r = 2 if registers[config]&4 else 2*(little(registers,rbase,3)+1)
        if vco/n/r != profile['output_hz']:
            raise ValueError('Output frequency mismatch')
    if writes[0x52a] != 1 or writes[0x536]&3 or writes[0x949] != 1 or writes[0x94a] != 1:
        raise ValueError('Expected manual IN0 selection')
    return {'p':str(p),'m':str(m),'vco_hz':int(vco),'output_hz':profile['output_hz']}
