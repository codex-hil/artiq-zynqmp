# Usage: vivado -mode batch -source program_genesys_pl.tcl -tclargs SERVER CABLE BITSTREAM
if {[llength $argv] != 3} {error "Require SERVER CABLE BITSTREAM"}
lassign $argv server cable bitstream
open_hw_manager
connect_hw_server -url $server
set matches {}
foreach target [get_hw_targets] {
    if {[lindex [split $target /] end] eq $cable} {lappend matches $target}
}
if {[llength $matches] != 1} {error "Cable $cable not uniquely identified"}
current_hw_target [lindex $matches 0]
open_hw_target
set devices [get_hw_devices -quiet xczu5*]
if {[llength $devices] != 1} {error "Expected one xczu5 on identified Genesys"}
set device [lindex $devices 0]
current_hw_device $device
set_property PROGRAM.FILE $bitstream $device
program_hw_devices $device
close_hw_manager
