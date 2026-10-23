# SPDX-License-Identifier: LGPL-3.0-or-later
# Parent holds Genesys lease. Read-only PERIPHERAL configuration/status, no force access.
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
puts "PERIPHERAL_BEGIN"
for {set sample 0} {$sample < 2} {incr sample} {
 foreach {name address} {
  gem0_network_control 0xff0b0000
  sd1_present_state 0xff170024 qspi_dma_status 0xff0f0708
 } {
  set value [mrd -address-space AP0 -value $address]
  puts [format "PERIPHERAL %d %s 0x%08x 0x%08x" $sample $name $address $value]
 }
 if {$sample == 0} {after 20}
}
puts "PERIPHERAL_END"
disconnect
