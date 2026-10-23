# SPDX-License-Identifier: LGPL-3.0-or-later
# Parent holds Genesys lease. Read-only PMUEVENT configuration/status, no force access.
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
puts "PMUEVENT_BEGIN"
for {set sample 0} {$sample < 2} {incr sample} {
 foreach {name address} {
  gpi1 0xffd40024 gpi2 0xffd40028 irq_pending 0xffd40034
  irq_enable 0xffd40038 gpi1_enable 0xffd60224 gpi2_enable 0xffd60228
 } {
  set value [mrd -address-space AP0 -value $address]
  puts [format "PMUEVENT %d %s 0x%08x 0x%08x" $sample $name $address $value]
 }
 if {$sample == 0} {after 20}
}
puts "PMUEVENT_END"
disconnect
