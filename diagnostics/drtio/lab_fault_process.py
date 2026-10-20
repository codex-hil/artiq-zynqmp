"""Bounded child/arm pump for the existing leased parent; LGPL-3.0-or-later.

No standalone entry point and no opening of hardware. Caller must already own
all board leases, verified identities and the exclusive UART, and restore in
its outer finally. This helper alone cannot qualify hardware or restoration.
"""
import json,os,re,subprocess,time
from pathlib import Path


def validate_request(request):
    if (not isinstance(request,dict) or set(request)!={'schema','token','request','cycles'} or type(request['schema']) is not int or request['schema']!=1 or
        request['request']!='arm-native-ddma-delay' or type(request['cycles']) is not int or request['cycles']!=250000 or
        not isinstance(request['token'],str) or not re.fullmatch('[0-9a-f]{32}',request['token'])):
        raise ValueError('Invalid laboratory arm request')


def acknowledge(directory,request):
    validate_request(request)
    p=Path(directory);ack=dict(schema=1,token=request['token'],status='ARMED_UART_VERIFIED',cycles=250000)
    temporary=p/'arm-ack.pending'
    with temporary.open('x') as f:json.dump(ack,f)
    try:os.link(temporary,p/'arm-ack.json')  # Publish complete JSON, never overwrite.
    finally:temporary.unlink()


def run(argv,*,directory,log,uart,raw,lease_fd,timeout=60,env=None):
    """Use only inside ExternalSession's all-board guarded lifetime.

    UART reads must already have a finite timeout. Child must receive only the
    parent's existing lease fd; no independent transport client is started.
    """
    if not 0<timeout<=120:raise ValueError('Bounded child timeout required')
    if getattr(uart,'timeout',None) is None or not 0<uart.timeout<=.5:
        raise ValueError('Existing UART must have a finite read timeout <=0.5s')
    directory=Path(directory);directory.mkdir(exist_ok=False)
    request_file=directory/'arm-request.json';armed=False;sent=False
    begin=len(raw);deadline=time.monotonic()+timeout
    child_env=dict(os.environ if env is None else env)
    child_env['ARTIQ_DDMA_LAB_HANDSHAKE']=str(directory.resolve())
    child_env['GENESYS_LEASE_FD']=str(lease_fd)
    with Path(log).open('x') as output:
        child=subprocess.Popen(argv,stdout=output,stderr=subprocess.STDOUT,env=child_env,pass_fds=(lease_fd,))
        try:
            request=None
            while True:
                raw.extend(uart.read(uart.in_waiting or 1))
                if request_file.exists() and not sent:
                    if request_file.stat().st_size>4096:raise ValueError('Oversized arm request')
                    request=json.loads(request_file.read_text())
                    # Validate before the only UART write; ack publication waits for hardware reply.
                    validate_request(request)
                    if uart.write(b'F')!=1:raise RuntimeError('Short laboratory arm UART write')
                    sent=True
                text=bytes(raw[begin:]).decode(errors='replace')
                replies=re.findall(r'^AUX_DDMA LAB_ARM result=(-?\d+) cycles=(\d+)\r?$',text,re.M)
                if len(replies)>1:raise RuntimeError('Duplicate arm confirmation')
                if replies and not armed:
                    if not sent or replies!=[('0','250000')]:raise RuntimeError('Unsolicited/refused arm')
                    acknowledge(directory,request);armed=True
                if 'AUX_DDMA LAB_ARM REFUSED' in text:raise RuntimeError('Arm eligibility refused')
                result=child.poll()
                if result is not None:
                    if result or not armed:raise RuntimeError('Experiment failed or exited without arm acknowledgement')
                    break
                if time.monotonic()>=deadline:raise TimeoutError('Bounded laboratory experiment timed out')
                time.sleep(.01)
        finally:
            if child.poll() is None:
                child.terminate()
                try:child.wait(timeout=3)
                except subprocess.TimeoutExpired:child.kill();child.wait(timeout=3)
    return Path(log).read_text()
