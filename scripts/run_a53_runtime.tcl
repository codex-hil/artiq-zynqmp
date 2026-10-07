# Usage: xsdb run_a53_runtime.tcl SERVER_URL ELF CABLE_SERIAL
if {[llength $argv] != 3} {error "Require SERVER_URL ELF CABLE_SERIAL"}
lassign $argv server elf cable_serial
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
select_genesys_target "Cortex-A53 #0"
catch {stop}
select_genesys_target PSU
puts "BOOT_MODE_BEFORE=[mrd 0xFF5E0200]"
set state [mrd -value 0xFD070004]
if {($state & 7) != 1} {error "DDR controller is not in normal mode: $state"}
puts "DDR_CONTROLLER_NORMAL"
select_genesys_target "Cortex-A53 #0"
rst -processor -clear-registers
catch {stop}
dow $elf
con
puts "A53_RUNTIME_STARTED_CPU1_PRESERVED"
disconnect
