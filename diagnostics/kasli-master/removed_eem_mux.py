"""Explicit board-modification overlay. LGPL-3.0-or-later."""
def apply(source):
    old = '        i2c::switch_select(BUSNO, 0x70, 0)?;\n'
    if source.count(old) != 1:
        raise ValueError('Review changed upstream EEM mux initialization')
    return source.replace(old, '        // EEM mux0x70 physically removed on this laboratory board.\n')
