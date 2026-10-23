# SPDX-License-Identifier: LGPL-3.0-or-later
# Parent holds Genesys lease. Read-only RPU configuration/status, no force access.
if {[llength $argv] != 2} {error "Require SERVER CABLE"}
lassign $argv server cable
if {$cable ne "210383B7F02DA"} {error "Wrong cable"}
connect -url $server
set ids {}
foreach p [targets -target-properties -filter {name == "PSU"}] {
 if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend ids [dict get $p target_id]}
}
if {[llength $ids] != 1} {error "PSU not unique"}
targets -set [lindex $ids 0]
puts "RPU_BEGIN"
for {set sample 0} {$sample < 2} {incr sample} {
 foreach {name address} {
  global_control 0xff9a0000 r50_config 0xff9a0100 r50_status 0xff9a0104
  r51_config 0xff9a0200 r51_status 0xff9a0204
  clock_control 0xff5e0090 reset_control 0xff5e023c
 } {
  set value [mrd -address-space AP0 -value $address]
  puts [format "RPU %d %s 0x%08x 0x%08x" $sample $name $address $value]
 }
 if {$sample == 0} {after 20}
}
puts "RPU_END"
disconnect
