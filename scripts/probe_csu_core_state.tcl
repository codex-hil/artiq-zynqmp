# SPDX-License-Identifier: LGPL-3.0-or-later
# Parent holds Genesys lease. Read-only STS and target metadata, no force access.
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
puts "CSU_BEGIN"
for {set sample 0} {$sample < 2} {incr sample} {
 foreach address {0xffc80008 0xffc80808} {
  set value [mrd -address-space AP0 -value $address]
  puts [format "CSU %d 0x%08x 0x%08x" $sample $address $value]
 }
 if {$sample == 0} {after 20}
}
puts "CSU_END"
# Metadata does not prove cache state, bus quiescence or held-reset semantics.
foreach name {"Cortex-A53 #0" "Cortex-A53 #1" "Cortex-A53 #2" "Cortex-A53 #3" "Cortex-R5 #0" "Cortex-R5 #1"} {
 set found {}
 foreach p [targets -target-properties -filter "name == \"$name\""] {
  if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend found $p}
 }
 if {[llength $found] > 1} {error "Duplicate core metadata: $name"}
 if {[llength $found] == 0} {puts "CORE_METADATA $name MISSING_NOT_PROVEN"} else {
  puts "CORE_METADATA $name [lindex $found 0]"
 }
}
disconnect
