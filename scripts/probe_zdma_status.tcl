# SPDX-License-Identifier: LGPL-3.0-or-later
# Fixed read-only plan. Parent holds Genesys lease. No force-access mode.
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
puts "ZDMA_BEGIN"
for {set sample 0} {$sample < 2} {incr sample} {
 set channel 0
 foreach base {0xfd500000 0xfd510000 0xfd520000 0xfd530000 0xfd540000 0xfd550000 0xfd560000 0xfd570000 0xffa80000 0xffa90000 0xffaa0000 0xffab0000 0xffac0000 0xffad0000 0xffae0000 0xffaf0000} {
  foreach {name offset} {status 0x11c control2 0x200} {
   set address [expr {$base+$offset}]
   set value [mrd -address-space AP0 -value $address]
   puts [format "ZDMA %d %d %s 0x%08x 0x%08x" $sample $channel $name $address $value]
  }
  incr channel
 }
 if {$sample == 0} {after 20}
}
puts "ZDMA_END"
disconnect
