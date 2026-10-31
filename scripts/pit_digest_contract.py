# SPDX-License-Identifier: LGPL-3.0-or-later
"""Host reference for proposed digest bytes; no target producer or HW admission."""
import hashlib,struct
PROFILE='pit-digest-canonical-host-reference-v1'

def sample_digest(record,expected_nonce):
    if type(record) is not bytes or len(record)!=48:
        raise ValueError('exact immutable 48-byte sample record required')
    if type(expected_nonce) is not int or not 0<expected_nonce<2**64:
        raise ValueError('nonzero u64 nonce required')
    complete,version,nonce,*values=struct.unpack('<IIQ8I',record)
    if (complete,version,nonce)!=(1,1,expected_nonce):
        raise ValueError('incomplete, wrong-version or wrong-session record')
    return hashlib.sha256(record).digest()

def image_digest(artifact):
    if type(artifact) is not bytes or not artifact:
        raise ValueError('nonempty immutable exact artifact bytes required')
    return hashlib.sha256(artifact).digest()

def digest_words(digest):
    if type(digest) is not bytes or len(digest)!=32:
        raise ValueError('exact SHA256 byte string required')
    return struct.unpack('<8I',digest)
