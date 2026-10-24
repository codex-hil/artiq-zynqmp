# SPDX-License-Identifier: LGPL-3.0-or-later
# Caller must hold shared Genesys lease. Fixed non-clearing reads only.
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
puts "AIB_BEGIN"
for {set sample 0} {$sample < 2} {incr sample} {
 foreach {name address} {request_before 0xff413030 type 0xff413038 ack 0xff413040 request_after 0xff413030} {
  set value [mrd -address-space AP0 -value $address]
  puts [format "AIB %d %s 0x%08x 0x%08x" $sample $name $address $value]
 }
 if {$sample == 0} {after 20}
}
puts "AIB_END"
disconnect
