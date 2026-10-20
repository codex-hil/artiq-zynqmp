"""Explicit volatile, locally administered unicast identity. LGPL-3.0-or-later."""
import re
DEFAULT='02:4b:03:48:48:54'


def literal(mac):
    if not isinstance(mac,str) or not re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}',mac):
        raise ValueError('Six colon-separated MAC bytes required')
    values=bytes.fromhex(mac.replace(':',''))
    if values[0]&3!=2:raise ValueError('Locally administered unicast MAC required')
    return 'EthernetAddress(['+', '.join('0x%02x'%v for v in values)+'])'


def apply(source,mac):
    old='let hardware_addr = '+literal(DEFAULT)+';'
    if source.count(old)!=1:raise ValueError('Unexpected volatile network overlay shape')
    return source.replace(old,'let hardware_addr = '+literal(mac)+';')
