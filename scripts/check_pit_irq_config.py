# SPDX-License-Identifier: LGPL-3.0-or-later
"""Initial ELF configuration dependency only, never live state or no-write proof."""
import re,hashlib
from package_local_candidate import loads

def check(data,symbols):
 machine,entry,segs=loads(data)
 if machine!=189 or entry!=0xffdc0050:raise ValueError('expected full MicroBlaze ELF')
 rows=re.findall(r'^([0-9a-f]+) ([0-9a-f]+) D XMicroblaze_ConfigTable$',symbols,re.M)
 if rows!=[('ffdd8b68','00000138')]:raise ValueError('unexpected unique config table range')
 address,size=0xffdd8b68,0x138
 spans=[s for s in segs if s['address']<=address and address+size<=s['address']+s['filesz']]
 if len(spans)!=1:raise ValueError('config not uniquely file-backed')
 s=spans[0];table=s['payload'][address-s['address']:address-s['address']+size]
 value=int.from_bytes(table[44:48],'little')
 if value!=1:raise ValueError('changed initial UseMsrInstr')
 return dict(status='INITIAL_ELF_CONFIG_ONE_NOT_LIVE_STATE',hardware_executed=False,deployable=False,
             table_address=address,table_bytes=size,table_sha256=hashlib.sha256(table).hexdigest(),
             field_offset=44,field_address=address+44,initial_value=value,
             live_value_observed=False,later_writes_excluded=False,
             limits='Initial bytes only. Does not prove loader execution, pointer immutability, no aliases/writers, exceptions or live helper selection.')
