#!/usr/bin/env python3
"""Reject incomplete, duplicated or incorrectly paged physical UART dumps."""
import argparse
import hashlib
import json
from pathlib import Path
import re

def parse(raw):
 if b'SI5342_READONLY_END PASS' not in raw:raise ValueError('Readout did not pass')
 rows=re.findall(rb'^REG ([0-9A-Fa-f]{4}) ([0-9A-Fa-f]{2})\r?$',raw.replace(b'\r\n',b'\n'),re.M)
 if len(rows)!=3072:raise ValueError('Expected exactly 3072 register rows')
 regs={int(a,16):int(b,16) for a,b in rows}
 if len(regs)!=3072 or set(regs)!=set(range(3072)):raise ValueError('Missing or duplicate addresses')
 if regs[2]!=0x42 or regs[3]!=0x53:raise ValueError('Wrong chip identity')
 if any(regs[(page<<8)+1]!=page for page in range(12)):raise ValueError('Page selector verification failed')
 return {'kind':'physical-register-backup','identity':'Si5342','revision':regs[5],
         'page_selectors_verified':12,'uart_sha256':hashlib.sha256(raw).hexdigest(),
         'registers':{f'{a:04x}':v for a,v in regs.items()}}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('uart',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 a.output.write_text(json.dumps(parse(a.uart.read_bytes()),indent=2)+'\n')
