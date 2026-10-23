# SPDX-License-Identifier: LGPL-3.0-or-later
# Parent holds Genesys lease. Documented external PMU RAM AXI access only.
if {[llength $argv] != 4} {error "Require SERVER CABLE NONCE_LO NONCE_HI"}
lassign $argv server cable nonce_lo nonce_hi
if {$cable ne "210383B7F02DA"} {error "Wrong cable"}
foreach value [list $nonce_lo $nonce_hi] {
 if {![string is entier -strict $value] || $value < 0 || $value > 0xffffffff} {error "Bad nonce word"}
}
if {($nonce_lo | $nonce_hi) == 0} {error "Zero nonce"}
connect -url $server
set ids {}
foreach p [targets -target-properties -filter {name == "PSU"}] {
 if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend ids [dict get $p target_id]}
}
if {[llength $ids] != 1} {error "PSU not unique"}
targets -set [lindex $ids 0]
# Exact new-image BSS layout. Kind2 asks PMU to clear IE and enter lab loop.
# No direct interrupt-register write; baseline PMU bootstrap required before reset.
foreach {address count} {0xffdd7f20 8 0xffdd7f68 16} {
 set initial [mrd -address-space AP0 -value $address $count]
 if {[llength $initial] != $count} {error "Incomplete initial record"}
 foreach value $initial {if {$value != 0} {error "Request/echo not fresh BSS"}}
}
set checksum [expr {(0x504d5551 ^ 2 ^ $nonce_lo ^ $nonce_hi ^ 1 ^ 2) & 0xffffffff}]
set payload [list 0 $nonce_lo $nonce_hi 1 0 2 $checksum 0]
mwr -address-space AP0 0xffdd7f20 0
for {set i 1} {$i < 8} {incr i} {
 mwr -address-space AP0 [expr {0xffdd7f20+4*$i}] [lindex $payload $i]
}
set readback [mrd -address-space AP0 -value 0xffdd7f20 8]
if {[llength $readback] != 8} {error "Incomplete request readback"}
for {set i 0} {$i < 8} {incr i} {
 if {[lindex $readback $i] != [lindex $payload $i]} {error "Request readback mismatch before publication"}
}
mwr -address-space AP0 0xffdd7f20 2
if {[mrd -address-space AP0 -value 0xffdd7f20] != 2} {error "Commit readback failed"}
puts "PMU_GUARD_BEGIN"
for {set sample 0} {$sample < 4} {incr sample} {
 after 100
 set before [mrd -address-space AP0 -value 0xffdd7f68]
 set words [mrd -address-space AP0 -value 0xffdd7f68 16]
 set after_seq [mrd -address-space AP0 -value 0xffdd7f68]
 if {[llength $words] != 16} {error "Incomplete echo"}
 puts [format "PMU_GUARD %d before 0x%08x" $sample $before]
 for {set i 0} {$i < 16} {incr i} {
  puts [format "PMU_GUARD %d word%d 0x%08x" $sample $i [lindex $words $i]]
 }
 puts [format "PMU_GUARD %d after 0x%08x" $sample $after_seq]
}
puts "PMU_GUARD_END"
disconnect
