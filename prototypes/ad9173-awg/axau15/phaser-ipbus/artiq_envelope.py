"""Stage-one ARTIQ driver: IPbus ARM/upload, scheduled RTIO START/ABORT.

Use only with EnvelopeRTIO or EnvelopeRTIOBridge connected by the satellite
integration. An IPbus-only image has no RTIO channel for this driver.
"""
from artiq.language.core import kernel
from artiq.coredevice.rtio import rtio_output


class PhaserEnvelope:
    kernel_invariants = {'core', 'channel'}

    def __init__(self, dmgr, channel, core_device='core'):
        self.core = dmgr.get(core_device)
        self.channel = channel

    @kernel
    def start(self, arm_id):
        """Consume one IPbus ARM token at the current RTIO timestamp."""
        if arm_id < 0 or arm_id >= 0x40000000:
            raise ValueError('Invalid envelope ARM token')
        rtio_output(self.channel << 8, (arm_id << 2) | 1)

    @kernel
    def abort(self):
        """Cancel playback/ARM and hold both envelopes at zero."""
        rtio_output(self.channel << 8, 2)

    @kernel
    def query(self):
        """Request an untimestamped input response; does not alter playback."""
        rtio_output(self.channel << 8, 0)
