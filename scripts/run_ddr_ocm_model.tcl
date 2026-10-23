# SPDX-License-Identifier: LGPL-3.0-or-later
# Called only from inherited-lease trained observer child.
if {[llength $argv] != 3} {error "Require SERVER ELF CABLE"}
lassign $argv server elf cable
if {$cable ne "210383B7F02DA"} {error "Wrong cable"}
source [file join [file dirname [info script]] load_ddr_ocm_model.tcl]
connect -url $server
set ids {}
foreach p [targets -target-properties -filter {name == "Cortex-A53 #0"}] {
 if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend ids [dict get $p target_id]}
}
if {[llength $ids] != 1} {error "CPU0 not unique"}
targets -set [lindex $ids 0]
fsbl_entry::selected_halted
ddr_model::run $elf
disconnect
