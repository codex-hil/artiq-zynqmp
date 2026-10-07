"""Physical RTIO timeline + empty input FIFO, without driving output pins."""
from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.rtio import rtio_input_timestamp, rtio_input_data, rtio_output
from numpy import int32, int64

@compile
class GenesysRTIOProbe(EnvExperiment):
    core: KernelInvariant[Core]

    def build(self):
        self.setattr_device("core")

    @rpc
    def report(self, before: int64, after: int64, counter: int64, empty: int64, scheduled: int64, sampled: int64, data: int32):
        if before != 0x1234567887654321 or after != before + 125 or counter <= 0 or empty != -1:
            raise ValueError("Incorrect RTIO CSR timeline/input result")
        if sampled < scheduled or sampled > scheduled + 32:
            raise ValueError("Scheduled RTIO input sample timestamp mismatch")
        if data != 0 and data != 1:
            raise ValueError("Invalid sampled physical input bit")
        print("RTIO_SAMPLE_PASS", scheduled, sampled, data, flush=True)
        print("RTIO_CSR_PASS", hex(before), hex(after), counter, empty, flush=True)

    @kernel
    def run(self):
        self.core.reset()
        at_mu(int64(0x1234567887654321))
        before = now_mu()
        delay_mu(int64(125))
        after = now_mu()
        empty = rtio_input_timestamp(int64(0), int32(1))
        counter = self.core.get_rtio_counter_mu()
        scheduled = counter + int64(1250000)
        at_mu(scheduled)
        # Channel 1 address 3 samples input and leaves sensitivity disabled.
        # This submits a real output event to the input PHY, not to JB1.
        rtio_output(int32(0x103), int32(0))
        sampled = rtio_input_timestamp(scheduled + int64(1250000), int32(1))
        at_mu(scheduled + int64(2500000))
        rtio_output(int32(0x103), int32(0))
        data = rtio_input_data(int32(1))
        self.report(before, after, counter, empty, scheduled, sampled, data)
