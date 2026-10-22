# SPDX-License-Identifier: LGPL-3.0-or-later
# Metadata only: no stop/reset/download/memory/register writes.
if {[llength $argv] != 2} {error "Require SERVER CABLE"}
lassign $argv server cable
if {$cable ne "210383B7F02DA"} {error "Wrong cable"}
connect -url $server
set ids {}
foreach p [targets -target-properties -filter {name == "Cortex-A53 #0"}] {
    if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {
        lappend ids [dict get $p target_id]
    }
}
if {[llength $ids] != 1} {error "CPU0 not uniquely identified"}
targets -set [lindex $ids 0]
puts "REGISTER_DEFINITIONS_BEGIN"
puts [rrd -defs]
puts "REGISTER_DEFINITIONS_END"
disconnect
