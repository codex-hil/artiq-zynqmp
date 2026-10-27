"""Offline symbol ownership check; never a physical admission. LGPL-3.0-or-later."""
import re


def check(text):
    symbols = {}
    for line in text.splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]+) (?:([0-9a-fA-F]+) )?([A-Za-z?]) (\S+)', line)
        if match:
            name = match[4]
            if name in symbols:
                raise ValueError('duplicate symbol')
            symbols[name] = (int(match[1], 16), int(match[2], 16) if match[2] else 0, match[3])
    try:
        address, size, kind = symbols['pit_capture_slot_layout_probe']
        bsslo = symbols['__bss_start'][0]
        bsshi = symbols['__bss_end'][0]
        stacklo = symbols['_stack_end'][0]
        stackhi = symbols['_stack'][0]
    except KeyError as exc:
        raise ValueError('missing layout symbol') from exc
    if size != 48 or kind not in ('b', 'B') or address % 4:
        raise ValueError('slot must be aligned 48-byte BSS object')
    if not 0xffdc0000 <= bsslo <= address < address + size <= bsshi <= stacklo < stackhi <= 0xffddf6e0:
        raise ValueError('slot/BSS/stack/table range conflict')
    for name, (start, length, typ) in symbols.items():
        if name == 'pit_capture_slot_layout_probe' or not length:
            continue
        if start < address + size and address < start + length:
            raise ValueError('slot overlaps sized symbol: ' + name)
    return {'slot': hex(address), 'bytes': size, 'stack_start': hex(stacklo),
            'stack_end_exclusive': hex(stackhi), 'hardware_executed': False,
            'physical_backend_ready': False, 'destructive_test_allowed': False,
            'scope': 'Symbol ranges only; linker/ELF initialization/lifetime and access path require separate review'}
