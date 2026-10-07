# Usage: xsdb reset_genesys_ps.tcl SERVER_URL CABLE_SERIAL
# Volatile PS reset; DDR initialization must be repeated by PMU + FSBL.
if {[llength $argv] != 2} {error "Require SERVER_URL CABLE_SERIAL"}
lassign $argv server cable_serial
proc select_genesys_target {name} {
    global cable_serial
    set matches {}
    foreach properties [targets -target-properties -filter "name == \"$name\""] {
        if {[dict exists $properties jtag_cable_serial] && [dict get $properties jtag_cable_serial] eq $cable_serial} {
            lappend matches [dict get $properties target_id]
        }
    }
    if {[llength $matches] != 1} {error "Target $name on $cable_serial not uniquely identified"}
    targets -set [lindex $matches 0]
}
connect -url $server
for {set i 0} {$i < 4} {incr i} {select_genesys_target "Cortex-A53 #$i"; catch {stop}}
select_genesys_target "Cortex-A53 #0"
rst -system
after 3000
puts "PS_SYSTEM_RESET_DONE"
disconnect
