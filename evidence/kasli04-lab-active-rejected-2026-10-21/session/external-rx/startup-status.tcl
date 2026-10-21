lassign $argv server cable
if {$cable ne "210383B7F02DA"} {error "Wrong Genesys cable"}
connect -url $server
set matches {}
foreach p [targets -target-properties -filter {name == "PSU"}] {
if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}
}
if {[llength $matches]!=1} {error "Exact Genesys target missing"}
targets -set [lindex $matches 0]
configparams force-mem-accesses 1
puts "AUX_STARTUP_STATUS monitor_magic [expr {wide([mrd -value 2684354560]) & 0xffffffff}]"
puts "AUX_STARTUP_STATUS monitor_reset [expr {wide([mrd -value 2684354564]) & 0xffffffff}]"
puts "AUX_STARTUP_STATUS monitor_tx_enable [expr {wide([mrd -value 2684354568]) & 0xffffffff}]"
puts "AUX_STARTUP_STATUS monitor_loopback [expr {wide([mrd -value 2684354572]) & 0xffffffff}]"
puts "AUX_STARTUP_STATUS monitor_status [expr {wide([mrd -value 2684354588]) & 0xffffffff}]"
puts "AUX_STARTUP_STATUS aux_in_reset [expr {wide([mrd -value 2684360732]) & 0xffffffff}]"
puts "AUX_STARTUP_STATUS aux_rx_up [expr {wide([mrd -value 2684360728]) & 0xffffffff}]"
puts "AUX_STARTUP_STATUS_COMPLETE"
disconnect
