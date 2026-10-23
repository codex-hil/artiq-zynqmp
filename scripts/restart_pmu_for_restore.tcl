# SPDX-License-Identifier: LGPL-3.0-or-later
# Parent holds Genesys lease and verifies baseline ELF hash. No DDR writer active.
# Explicit pre-reset bootstrap: do not depend on parked PMU servicing system reset.
if {[llength $argv] != 3} {error "Require SERVER BASELINE_PMU CABLE"}
lassign $argv server elf cable
if {$cable ne "210383B7F02DA"} {error "Wrong cable"}
connect -url $server
set ids {}
foreach p [targets -target-properties -filter {name == "MicroBlaze PMU"}] {
 if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend ids [dict get $p target_id]}
}
if {[llength $ids] != 1} {error "PMU not unique"}
targets -set [lindex $ids 0]
stop
set halted 0
for {set i 0} {$i <= 20} {incr i} {
 set rows [targets -target-properties -filter {is_current == 1}]
 if {[llength $rows] != 1} {error "Selected PMU not unique"}
 set p [lindex $rows 0]
 if {[dict get $p name] ne "MicroBlaze PMU" || [dict get $p jtag_cable_serial] ne $cable} {error "PMU identity changed"}
 if {[dict exists $p suspended] && [dict get $p suspended]} {set halted 1;break}
 if {$i < 20} {after 50}
}
if {!$halted} {error "PMU debug halt unconfirmed; no download"}
dow $elf
con
after 500
puts "PMU_RESTORE_BOOTSTRAP_STARTED"
# This marker alone is not restoration PASS; full normal reset/boot/tests required.
disconnect
