"""Stage-one ARTIQ driver: IPbus ARM/upload, scheduled RTIO START/ABORT.

Use only with EnvelopeRTIO or EnvelopeRTIOBridge connected by the satellite
integration. An IPbus-only image has no RTIO channel for this driver.
"""
from artiq.language.core import kernel
from artiq.coredevice.rtio import rtio_output, rtio_input_timestamped_data


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

    @kernel
    def read_response(self, deadline_mu):
        """Consume one response by an absolute RTIO deadline (machine units).

        Call once per admitted command, in FIFO order. A timeout does not
        cancel playback or prove START was not executed. Late replies require
        explicit recovery before another command; never retry automatically.
        This does not advance the timeline or confirm playback completion.
        """
        if deadline_mu < 0:
            raise ValueError('Invalid envelope response deadline')
        timestamp, response = rtio_input_timestamped_data(deadline_mu, self.channel)
        if timestamp == -1:
            raise ValueError('Envelope RTIO response timeout')
        return response

    @kernel
    def check_response(self, deadline_mu):
        """Consume one response; raise on rejection, return state bits on success.

        The same blocking/ordering rules as read_response apply. This may
        consume timeline slack; replenish it before scheduling another output.
        """
        if deadline_mu < 0:
            raise ValueError('Invalid envelope response deadline')
        timestamp, response = rtio_input_timestamped_data(deadline_mu, self.channel)
        if timestamp == -1:
            raise ValueError('Envelope RTIO response timeout')
        if response < 0 or response > 0x3f:
            raise ValueError('Invalid envelope RTIO response')
        result = response & 0xf
        if result == 1:
            raise ValueError('Invalid envelope RTIO command')
        if result == 2:
            raise ValueError('Envelope is not armed or ready')
        if result == 3:
            raise ValueError('Stale envelope ARM token')
        if result == 4:
            raise ValueError('Envelope timeline is disabled')
        if result != 0:
            raise ValueError('Unknown envelope RTIO result')
        return response
