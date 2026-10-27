"""Offline terminal-intent receipt: never proof of sleep. LGPL-3.0-or-later."""
import hashlib
import re
import struct
from pit_counter_observation import _uint
from pit_publication import accept as accept_samples

FORMAT = struct.Struct('<4IQ2I32s32s')
MAGIC = 0x50545331
STATUSES = {1: 'IRQ_UNPROVEN', 2: 'READ_FAILED', 3: 'PUBLICATION_UNKNOWN',
            4: 'CAPTURE_COMPLETE'}


def accept(first, second, nonce, image_sha256, samples=None):
    """Check supplied bytes and bindings only; no physical reader or writer."""
    _uint(nonce, 64, True)
    if type(image_sha256) is not str or not re.fullmatch('[0-9a-f]{64}', image_sha256) or image_sha256 == '0' * 64:
        raise ValueError('nonzero lowercase image SHA256 required')
    if type(first) is not bytes or type(second) is not bytes or len(first) != FORMAT.size or first != second:
        raise ValueError('two equal exact immutable terminal snapshots required')
    commit, magic, version, status, session, checked_msr, final_msr, image, sample_hash = FORMAT.unpack(first)
    if commit != 1 or magic != MAGIC or version != 1 or status not in STATUSES:
        raise ValueError('uncommitted or unsupported terminal record')
    if session != nonce or image != bytes.fromhex(image_sha256):
        raise ValueError('terminal session/image mismatch')
    if samples is not None and (type(samples) is not bytes or len(samples) != 48):
        raise ValueError('exact sample bytes or explicit absence required')
    expected = hashlib.sha256(samples).digest() if samples is not None else bytes(32)
    if sample_hash != expected:
        raise ValueError('terminal sample binding mismatch')
    observation = None
    if status == 4:
        if samples is None or checked_msr & 2 or final_msr != checked_msr:
            raise ValueError('capture-complete requires samples and matching IE-clear MSR')
        observation = accept_samples(samples, samples, nonce)
    return {'status': STATUSES[status], 'samples': observation,
            'scope': 'Untrusted supplied terminal-intent bytes; hashes bind content, not origin or actual execution',
            'terminal_intent': 'SLEEP_REQUESTED_UNOBSERVED', 'sleep_proven': False,
            'hardware_executed': False, 'physical_backend_ready': False,
            'destructive_test_allowed': False}
