"""Bounded file handshake with the future all-board wrapper; LGPL-3.0-or-later.

No UART or hardware access. Wrapper must obtain leases, verify live identity,
write UART F, verify LAB_ARM result=0, and only then atomically publish the ack.
Acknowledgement alone is not active-fault evidence.
"""
import json,time,secrets,tempfile,os
from pathlib import Path


def request(directory):
    directory=Path(directory)
    if not directory.is_dir():raise ValueError('Existing fresh session handshake directory required')
    if (directory/'arm-ack.json').exists():raise ValueError('Stale arm acknowledgement')
    token=secrets.token_hex(16)
    payload=dict(schema=1,token=token,request='arm-native-ddma-delay',cycles=250000)
    with tempfile.NamedTemporaryFile(mode='w',dir=directory,prefix='arm-request-',suffix='.pending',delete=False) as f:
        temporary=Path(f.name);json.dump(payload,f)
    try:os.link(temporary,directory/'arm-request.json')
    finally:temporary.unlink()
    return token


def wait(directory,token,timeout=10):
    if not 0<=timeout<=30:raise ValueError('Handshake timeout must be 0..30 seconds')
    path=Path(directory)/'arm-ack.json';deadline=time.monotonic()+timeout
    while True:
        if path.exists():
            ack=json.loads(path.read_text())
            if ack!=dict(schema=1,token=token,status='ARMED_UART_VERIFIED',cycles=250000):
                raise ValueError('Wrong/stale/failed arm acknowledgement')
            return
        if time.monotonic()>=deadline:raise TimeoutError('Guarded wrapper did not acknowledge laboratory arm')
        time.sleep(min(.02,max(0,deadline-time.monotonic())))


def arm(directory):
    token=request(directory)
    wait(directory,token)
