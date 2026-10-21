lassign $argv server cable
connect -url $server
set matches {}
foreach p [targets -target-properties -filter {name == "PSU"}] {
if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}
}
if {[llength $matches]!=1} {error "Exact Genesys target missing"}
targets -set [lindex $matches 0]
configparams force-mem-accesses 1
if {[expr {wide([mrd -value 2684354560]) & 0xffffffff}] != 0x44525430} {error "Wrong PL"}
mwr 2684354564 1
after 1000
mwr 2684354564 0
puts "GENESYS_GTH_RESET_RELEASED"
disconnect
