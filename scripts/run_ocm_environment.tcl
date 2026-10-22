# Dedicated OCM observation loader; LGPL-3.0-or-later.
# Derived from the existing OCM bring-up flow; exact cable and strict core stops.
if {[llength $argv] != 4} {error "Require SERVER_URL ELF PSU_INIT_TCL CABLE_SERIAL"}
lassign $argv server elf psu_init cable_serial
if {$cable_serial ne "210383B7F02DA"} {error "Wrong Genesys cable"}
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
for {set i 0} {$i < 4} {incr i} {
 select_genesys_target "Cortex-A53 #$i"
 stop
}
select_genesys_target PSU
source $psu_init
# Reuse generated AMD MIO/clock/peripheral setup, explicitly exclude DDR.
init_ps [subst {$psu_mio_init_data $psu_peripherals_pre_init_data $psu_pll_init_data $psu_clock_init_data $psu_peripherals_init_data $psu_resetin_init_data $psu_resetout_init_data}]
init_peripheral
puts "PS_UART_CLOCK_INIT_DONE_NO_DDR"
select_genesys_target "Cortex-A53 #0"
rst -processor -clear-registers
stop
dow $elf
con
puts "OCM_DIAGNOSTIC_STARTED"
disconnect
