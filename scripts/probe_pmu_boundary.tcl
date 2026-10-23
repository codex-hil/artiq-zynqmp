# SPDX-License-Identifier: LGPL-3.0-or-later
# Parent holds Genesys lease. Documented external PMU RAM AXI access only.
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
puts "PMU_BOUNDARY_BEGIN"
for {set sample 0} {$sample < 4} {incr sample} {
 set before [mrd -address-space AP0 -value 0xffdd7cf4]
 set words [mrd -address-space AP0 -value 0xffdd7cf4 8]
 set after_seq [mrd -address-space AP0 -value 0xffdd7cf4]
 if {[llength $words] != 8} {error "Incomplete PMU record"}
 puts [format "PMU_BOUNDARY %d before 0x%08x" $sample $before]
 for {set i 0} {$i < 8} {incr i} {
  puts [format "PMU_BOUNDARY %d word%d 0x%08x" $sample $i [lindex $words $i]]
 }
 puts [format "PMU_BOUNDARY %d after 0x%08x" $sample $after_seq]
 if {$sample < 3} {after 20}
}
puts "PMU_BOUNDARY_END"
disconnect
