"""Read-only AUX admission telemetry under the parent Genesys lease.

LGPL-3.0-or-later. Samples are sequential, not an atomic clock snapshot.
"""
import re

REGISTERS = ("monitor_magic", "monitor_reset", "monitor_tx_enable",
             "monitor_loopback", "monitor_status", "aux_in_reset", "aux_rx_up")


def script(mapping):
    lines = [
        'lassign $argv server cable',
        'if {$cable ne "210383B7F02DA"} {error "Wrong Genesys cable"}',
        'connect -url $server', 'set matches {}',
        'foreach p [targets -target-properties -filter {name == "PSU"}] {',
        'if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}',
        '}',
        'if {[llength $matches]!=1} {error "Exact Genesys target missing"}',
        'targets -set [lindex $matches 0]',
        'configparams force-mem-accesses 1',
    ]
    for name in REGISTERS:
        item = mapping['registers'][name]
        if item['words'] != 1:
            raise ValueError('Single-word startup status required: ' + name)
        address = int(item['address'])
        if address < 0 or address > 0xffffffff or address % 4:
            raise ValueError('Invalid status address')
        lines.append('puts "AUX_STARTUP_STATUS %s [expr {wide([mrd -value %d]) & 0xffffffff}]"' % (name, address))
    lines.extend(('puts "AUX_STARTUP_STATUS_COMPLETE"', 'disconnect'))
    return '\n'.join(lines) + '\n'


def parse(text):
    rows = re.findall(r'^AUX_STARTUP_STATUS (\w+) (\d+)\s*$', text, re.M)
    if [name for name, _ in rows] != list(REGISTERS) or text.count('AUX_STARTUP_STATUS_COMPLETE') != 1:
        raise ValueError('Incomplete/duplicate startup status telemetry')
    values = {name: int(value) for name, value in rows}
    if any(value > 0xffffffff for value in values.values()):
        raise ValueError('Status word outside u32')
    return {'registers': values, 'scope': 'post-failure sequential read-only sample; not exact failing poll or link qualification'}
