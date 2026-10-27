"""One-shot offline observation-to-receipt model. LGPL-3.0-or-later.

Input bytes/MSR/outcomes are supplied observations, NOT authenticated hardware.
No MMIO, ELF execution or target hashing implementation is provided.
"""
import hashlib
from pit_counter_observation import _uint
from pit_publication import accept as accept_samples
from pit_terminal_receipt import FORMAT, MAGIC


class ReceiptProducer:
    def __init__(self, image_bytes, nonce):
        _uint(nonce, 64, True)
        if type(image_bytes) is not bytes or not 0 < len(image_bytes) <= 1024 * 1024:
            raise ValueError('immutable image bytes, at most 1 MiB, required')
        self._image = hashlib.sha256(image_bytes).digest()
        self._nonce = nonce
        self._stage = 0

    def checked_irq(self, before, after):
        if self._stage != 0:
            raise ValueError('IRQ observation out of order')
        for value in (before, after):
            if value is not None:
                _uint(value, 32)
        self._before, self._after = before, after
        self._irq_ok = before is not None and after is not None and after == before & ~2
        self._stage = 1

    def sample_result(self, outcome, raw_bytes=None):
        if self._stage != 1:
            raise ValueError('sample observation out of order')
        if type(outcome) is not str or outcome not in ('READ_FAILED', 'PUBLICATION_UNKNOWN', 'COMPLETE', 'IRQ_UNPROVEN'):
            raise ValueError('unsupported sample outcome')
        if not self._irq_ok and (outcome != 'IRQ_UNPROVEN' or raw_bytes is not None):
            raise ValueError('failed initial IRQ check cannot capture or publish samples')
        if raw_bytes is not None and (type(raw_bytes) is not bytes or len(raw_bytes) != 48):
            raise ValueError('immutable exact sample frame or absence required')
        if outcome in ('READ_FAILED', 'IRQ_UNPROVEN') and raw_bytes is not None:
            raise ValueError('this outcome cannot have published sample bytes')
        if outcome == 'COMPLETE':
            if raw_bytes is None:
                raise ValueError('complete sample bytes required')
            accept_samples(raw_bytes, raw_bytes, self._nonce)
        self._sample = raw_bytes
        self._outcome = outcome
        self._stage = 2

    def finish(self, final_msr):
        if self._stage != 2:
            raise ValueError('terminal observation out of order or already consumed')
        self._stage = 3  # No retry even after invalid final observation.
        if final_msr is not None:
            _uint(final_msr, 32)
        status = {'IRQ_UNPROVEN': 1, 'READ_FAILED': 2, 'PUBLICATION_UNKNOWN': 3, 'COMPLETE': 4}[self._outcome]
        if not self._irq_ok or final_msr is None or final_msr != self._after:
            status = 1
        sample_hash = hashlib.sha256(self._sample).digest() if self._sample is not None else bytes(32)
        return FORMAT.pack(1, MAGIC, 1, status, self._nonce, self._after or 0,
                           final_msr or 0, self._image, sample_hash)
