# SPDX-License-Identifier: LGPL-3.0-or-later
# Caller must hold shared Genesys and plug leases. One read; no target stop/write.
if {[llength $argv] != 4} {error "Require SERVER CABLE NONCE_LO NONCE_HI"}
lassign $argv server cable lo hi
if {$cable ne "210383B7F02DA"} {error "Wrong cable"}
foreach value [list $lo $hi] {
 if {![string is entier -strict $value] || $value < 0 || $value > 0xffffffff} {error "Invalid nonce word"}
}
if {($lo | $hi) == 0} {error "Zero nonce"}
connect -url $server
try {
 set ids {}
 foreach p [targets -target-properties -filter {name == "PSU"}] {
  if {[dict exists $p name] && [dict get $p name] eq "PSU" && [dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend ids [dict get $p target_id]}
 }
 if {[llength $ids] != 1} {error "PSU not unique"}
 targets -set [lindex $ids 0]
 set words [mrd -address-space AP0 -value 0xffd80000 1]
 if {[llength $words] != 1 || ![string is entier -strict [lindex $words 0]] || [lindex $words 0] < 0 || [lindex $words 0] > 0xffffffff} {error "Invalid status response"}
 puts [format "PMU_SLEEP_STATUS %08x %08x %08x" $hi $lo [lindex $words 0]]
} finally {disconnect}
