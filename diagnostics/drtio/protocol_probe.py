"""Laboratory raw-GTH loopback using upstream ARTIQ RT/AUX link framing.

Not a satellite: no RTIO packets, AUX firmware, latency or remote-link claim.
New glue is LGPL-3.0-or-later; upstream codecs retain their notices.
"""
from migen import Module, Signal, Cat, If, Case, ClockDomainsRenamer
from migen.genlib.cdc import MultiReg
from misoc.interconnect.csr import AutoCSR, CSRStorage, CSRStatus
from artiq.gateware.drtio.link_layer import LinkLayerTX, LinkLayerRX
from raw20_codec import Raw20Codec
from monitor import GrayCounter

# Full K28.5 symbols, bit-reversed for the existing LSB-first encoder.
COMMAS = (0b0101111100, 0b1010000011)


class WordAligner(Module):
    """Acquire lane-zero comma in a two-word serial window; hold until reset.

    This lab fabric aligner does not replace GT buffer bypass/phase alignment.
    """
    def __init__(self):
        self.input = Signal(20)
        self.output = Signal(20)
        self.aligned = Signal()
        self.offset = Signal(5)
        previous = Signal(20)
        window = Signal(40)
        self.comb += window.eq(Cat(previous, self.input))
        self.sync += previous.eq(self.input)
        # Lowest offset wins if a word contains more than one comma.
        cases = []
        for i in range(20):
            match = (window[i:i+10] == COMMAS[0]) | (window[i:i+10] == COMMAS[1])
            cases.append((match, i))
        chain = None
        for match, i in reversed(cases):
            clause = If(match, self.aligned.eq(1), self.offset.eq(i))
            if chain is not None: clause = clause.Else(chain)
            chain = clause
        self.sync += If(~self.aligned, chain)
        self.comb += Case(self.offset, {i:self.output.eq(window[i:i+20]) for i in range(20)})


class ProtocolProbe(Module, AutoCSR):
    def __init__(self, phase_bits=12):
        self.enable = CSRStorage(1, name='enable')
        self.inject = CSRStorage(1, name='inject')
        self.alignment = CSRStatus(6, name='alignment')
        self.tx_raw = Signal(20)
        self.rx_raw = Signal(20)
        self.submodules.aligner = ClockDomainsRenamer('gth_rx')(WordAligner())
        self.submodules.codec = ClockDomainsRenamer({'sys':'gth_tx'})(Raw20Codec(rx_domain='gth_rx'))
        self.submodules.tx = ClockDomainsRenamer('gth_tx')(LinkLayerTX(self.codec.encoder))
        self.submodules.rx = ClockDomainsRenamer('gth_rx')(LinkLayerRX(self.codec.decoders))
        self.comb += [self.aligner.input.eq(self.rx_raw), self.codec.rx_raw.eq(self.aligner.output)]
        enabled, inject = Signal(), Signal()
        self.specials += [MultiReg(self.enable.storage,enabled,odomain='gth_tx'),
                          MultiReg(self.inject.storage,inject,odomain='gth_tx'),
                          MultiReg(Cat(self.aligner.aligned,self.aligner.offset),self.alignment.status)]
        if phase_bits < 8: raise ValueError("Frame period must leave at least 16 idle words")
        phase = Signal(phase_bits)
        self.sync.gth_tx += phase.eq(phase+1)
        rt_start = 1 << (phase_bits-4)
        aux_start = 1 << (phase_bits-1)
        rt = (phase >= rt_start) & (phase < rt_start+16) & enabled
        aux = (phase >= aux_start) & (phase < aux_start+16) & enabled
        self.comb += [self.tx.rt_frame.eq(rt), self.tx.rt_data.eq(0xa500 | phase[:4]),
                     self.tx.aux_frame.eq(aux), self.tx.aux_data.eq(phase[:4]),
                     self.tx_raw.eq(self.codec.tx_raw ^ (inject & rt))]
        # Corrupt a raw bit after encoding. Receiver must flag payload/framing
        # errors, not merely count locally generated TX packets.
        names=('rt_words','rt_frames','rt_errors','aux_words','aux_frames','aux_errors')
        self.counts={}
        for name in names:
            counter=GrayCounter('gth_rx')
            setattr(self.submodules,name+'_count',counter)
            counter.enable.reset=0
            self.counts[name]=counter
            reg=CSRStatus(32,name=name)
            setattr(self,name,reg)
            self.comb += reg.status.eq(counter.value)
        for kind in ('rt','aux'):
            frame=getattr(self.rx,kind+'_frame')
            data=getattr(self.rx,kind+'_data')
            stb=1 if kind=='rt' else self.rx.aux_stb
            previous=Signal()
            index=Signal(6)
            seen=Signal()
            start=frame & ~previous
            finish=~frame & previous
            sample=stb & self.aligner.aligned
            expected=Signal(16 if kind=='rt' else 4)
            self.comb += expected.eq((0xa500 if kind=='rt' else 0) | index[:4])
            # On first sample in a frame, expect sequence zero immediately.
            bad=Signal()
            self.comb += bad.eq((start & (data != (0xa500 if kind=='rt' else 0))) |
                                (~start & frame & ((data != expected) | (index >= 16))) |
                                (finish & seen & (index != 16)))
            self.comb += [self.counts[kind+'_words'].enable.eq(sample & frame),
                         self.counts[kind+'_frames'].enable.eq(sample & finish & seen),
                         self.counts[kind+'_errors'].enable.eq(sample & bad)]
            self.sync.gth_rx += If(sample,
                previous.eq(frame),
                If(start,index.eq(1),seen.eq(1)).Elif(frame,index.eq(index+1)))
