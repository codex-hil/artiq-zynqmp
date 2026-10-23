# SPDX-License-Identifier: LGPL-3.0-or-later
# Diagnostic bitstream only. Parent holds Genesys lease through restoration.
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
puts "DMA_OBSERVER_BEGIN"
for {set sample 0} {$sample < 2} {incr sample} {
 foreach address {0xa0003000 0xa0003004} {
  set value [mrd -address-space AP0 -value $address]
  puts [format "DMA_OBSERVER %d 0x%08x 0x%08x" $sample $address $value]
 }
 if {$sample == 0} {after 20}
}
puts "DMA_OBSERVER_END"
disconnect
