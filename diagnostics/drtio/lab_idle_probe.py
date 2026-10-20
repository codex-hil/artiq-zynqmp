"""Read-only idle probe using an existing leased UART; LGPL-3.0-or-later.

No standalone entrypoint or UART opening. Parent owns board identity, artifacts,
all leases and restoration. Two stable samples do not prove absolute timing.
"""
import re,time
FIELDS=('ready','epoch','active','pending','armed','holding','triggers','rejected',
        'arm_rejected','faulted','ar','rlast','edges','accepted','completed','raw')
PATTERN=r'^AUX_DDMA LAB_IDLE '+' '.join(name+r'=(\d+)' for name in FIELDS)+r'\r?$'


def parse(text):
    rows=[dict(zip(FIELDS,map(int,m.groups()))) for m in re.finditer(PATTERN,text,re.M)]
    if len(rows)!=2:raise ValueError('Exactly two complete idle samples required')
    if any(v>=2**32 for row in rows for v in row.values()):raise ValueError('Invalid CSR width')
    if rows[0]!=rows[1] or rows[0]['ready']!=1 or not rows[0]['epoch']:
        raise ValueError('Idle samples not ready/stable in one loaded epoch')
    if any(rows[0][name] for name in FIELDS if name not in ('ready','epoch','edges')):
        raise ValueError('Non-pristine DMA/arm/counter/error state')
    return dict(lab_idle_counters='PASS',lab_idle_samples=rows,
                lab_idle_scope='two read-only UART samples; pristine DMA; stable output edge count and TSC epoch')


def probe(uart,raw,timeout=2,settle=.05):
    if getattr(uart,'timeout',None) is None or not 0<uart.timeout<=.5:
        raise ValueError('Existing finite UART timeout required')
    if not 0<timeout<=5 or not .02<=settle<=1:raise ValueError('Bounded probe/settle required')
    start=len(raw)
    for index in range(2):
        if uart.write(b'I')!=1:raise RuntimeError('Short idle probe UART write')
        deadline=time.monotonic()+timeout
        while True:
            raw.extend(uart.read(uart.in_waiting or 1))
            text=bytes(raw[start:]).decode(errors='replace')
            count=len(list(re.finditer(PATTERN,text,re.M)))
            if count>index+1:raise RuntimeError('Duplicate/unrequested idle sample')
            if count==index+1:break
            if time.monotonic()>=deadline:raise TimeoutError('Read-only idle reply timed out')
            time.sleep(.01)
        if index==0:time.sleep(settle)
    return parse(bytes(raw[start:]).decode(errors='replace'))
