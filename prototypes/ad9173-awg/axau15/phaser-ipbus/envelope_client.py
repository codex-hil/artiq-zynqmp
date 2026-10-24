"""Finite complex envelopes over IPbus. Caller holds the shared board lease."""
import math
import time
from client import Phaser

CLOCK = 153600000
DEPTH = 256


def pack_gain(value):
    value = complex(value)
    if not math.isfinite(value.real) or not math.isfinite(value.imag) or abs(value) > 1.000000000001:
        raise ValueError('Envelope gain must lie within the complex unit circle')
    def quantize(v):return max(-32768, min(32767, round(v*32768)))
    return (quantize(value.real)&65535) | ((quantize(value.imag)&65535)<<16)


def encode_program(entries):
    """Each entry is (duration_in_JESD_cycles, complex_gain_ch0, complex_gain_ch1)."""
    entries = list(entries)
    if not 1 <= len(entries) <= DEPTH:raise ValueError('Program needs1..256 entries')
    words = []
    for duration, a, b in entries:
        if isinstance(duration, bool) or not isinstance(duration, int) or not 1 <= duration <= 0xffffffff:
            raise ValueError('Duration must be1..2^32-1 JESD cycles')
        words += [duration, pack_gain(a), pack_gain(b), 0]
    return words


class EnvelopePhaser(Phaser):
    def require_envelope(self):
        identity = self.identify()
        if identity['abi'] not in (0x10001, 0x10002) or not (self.read(8)[0]&1):
            raise RuntimeError('This image does not implement envelope playback')

    def playback_status(self):
        busy, state, commands = self.read(0x20, 3)
        return dict(busy=bool(busy), mode=bool(state&1), playing=bool(state&2),
                    result=(state>>4)&3, commands=commands)

    def load(self, entries):
        words = encode_program(entries)
        self.require_envelope()
        if self.read(0x20)[0]:raise RuntimeError('Envelope RAM is owned by playback')
        for offset in range(0, len(words), 128):self.write(0x400+offset, words[offset:offset+128])
        if self.block(0x400, len(words)) != words:raise RuntimeError('Envelope RAM readback mismatch')
        self.write(0x23, [len(words)//4])
        return words

    def start(self, repeats=1):
        if isinstance(repeats, bool) or not isinstance(repeats, int) or not 1 <= repeats <= 0xffffffff:
            raise ValueError('Repeat count must be1..2^32-1')
        self.require_envelope()
        if self.read(0x20)[0] or self.read(0x11)[0]:raise RuntimeError('Generator busy')
        self.write(0x24, [repeats])
        self.write(0x25, [1])  # Never retry an uncertain start response.

    def arm(self, repeats=1, timeout=2):
        """Reserve validated program until one RTIO START, completion or ABORT."""
        self.require_envelope()
        if self.identify()['abi'] != 0x10002 or not self.read(8)[0]&2:
            raise RuntimeError('Image has no scheduled-start interface')
        if isinstance(repeats, bool) or not isinstance(repeats, int) or not 1 <= repeats <= 0xffffffff:
            raise ValueError('Repeat count must be1..2^32-1')
        if self.read(0x20)[0] or self.read(0x11)[0]:raise RuntimeError('Generator busy')
        self.write(0x24, [repeats]);self.write(0x25, [3])
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            if self.read(0x27)[0]:return self.read(0x28)[0]
            if not self.playback_status()['busy']:raise RuntimeError('ARM rejected or cancelled')
            time.sleep(.001)
        raise TimeoutError('ARM pending; no automatic retry')

    def wait(self, timeout=2, allow_abort=False):
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            status = self.playback_status()
            if not status['busy']:
                if status['result'] not in ((0, 1) if allow_abort else (0,)):
                    raise RuntimeError('Envelope result '+str(status['result']))
                return status
            time.sleep(.001)
        raise TimeoutError('Envelope still busy; no automatic restart or abort')

    def abort(self):
        self.require_envelope()
        self.write(0x26, [1])
        return self.wait(allow_abort=True)

    def bypass(self):
        self.require_envelope()
        if self.read(0x20)[0]:raise RuntimeError('Abort or finish playback before bypass')
        self.write(0x25, [2])
        return self.wait()


def main():
    """Lease covers upload, finite playback and completion/abort."""
    import argparse
    import fcntl
    import json
    from pathlib import Path
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host', default='192.168.2.241')
    action = p.add_mutually_exclusive_group(required=True)
    action.add_argument('--play', type=Path, help='JSON list: [cycles, [I0,Q0], [I1,Q1]]')
    action.add_argument('--bypass', action='store_true', help='Return to continuous DDS')
    action.add_argument('--status', action='store_true')
    action.add_argument('--abort', action='store_true')
    p.add_argument('--repeats', type=int, default=1)
    p.add_argument('--timeout', type=float, default=10)
    a = p.parse_args()
    if not math.isfinite(a.timeout) or a.timeout <= 0:p.error('Positive finite timeout required')
    if not 1 <= a.repeats <= 0xffffffff:p.error('Repeat count must be1..2^32-1')
    entries = None
    if a.play:
        entries = [(duration, complex(*ch0), complex(*ch1)) for duration, ch0, ch1 in json.loads(a.play.read_text())]
        encode_program(entries)  # Validate before opening hardware.
    with open('/home/codex-hil/.cache/alinx-210512180081.lock', 'a+') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX|fcntl.LOCK_NB)
        c = EnvelopePhaser(a.host)
        try:
            c.require_envelope()
            if entries is not None:
                c.load(entries)
                try:
                    c.start(a.repeats)
                    c.wait(a.timeout)
                except BaseException:
                    # A lost START reply is uncertain: abort, never retry START.
                    c.abort()
                    raise
            elif a.bypass:c.bypass()
            elif a.abort:c.abort()
            print(json.dumps(c.playback_status(), indent=2))
        finally:
            if not a.status:
                from datetime import datetime, timezone
                state = Path('/home/codex-hil/.cache/alinx-210512180081.state.json')
                shared = json.loads(state.read_text()) if state.exists() else {}
                shared.update(updated_utc=datetime.now(timezone.utc).isoformat(), owner='envelope-client', host=a.host)
                try:shared['envelope'] = c.playback_status()
                except Exception as error:shared['envelope'] = {'status':'UNKNOWN', 'error':str(error)}
                tmp = state.with_suffix('.tmp');tmp.write_text(json.dumps(shared, indent=2)+'\n');tmp.replace(state)
            c.close()


if __name__ == '__main__':main()
