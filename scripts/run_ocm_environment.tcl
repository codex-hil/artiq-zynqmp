# Dedicated OCM observation loader; LGPL-3.0-or-later.
# Derived from the existing OCM bring-up flow; exact cable and checked core states.
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
# XSDB stop sends suspend even when a core is already stopped/reset. Only the
# exact backend POR error, repeated on the same selected target, admits reset.
# CPU0 after processor reset must be suspended, never admitted via POR.
proc admit_core {allow_por} {
    set props [lindex [targets -target-properties -filter {is_current == 1}] 0]
    if {![dict exists $props suspended]} {error "Missing core suspension state"}
    if {[dict get $props suspended]} {puts "CORE_ADMISSION SUSPENDED"; return}
    if {[catch {stop} message options]} {
        if {!$allow_por || $message ne "The core is held in power-on-reset"} {
            return -options $options $message
        }
        if {![catch {stop} repeated] || $repeated ne $message} {
            error "Power-on-reset state changed during admission"
        }
        puts "CORE_ADMISSION HELD_POWER_ON_RESET_CONFIRMED"
        return
    }
    set props [lindex [targets -target-properties -filter {is_current == 1}] 0]
    if {![dict exists $props suspended] || ![dict get $props suspended]} {
        error "Core did not become suspended"
    }
    puts "CORE_ADMISSION STOPPED_CONFIRMED"
}
connect -url $server
# Debugger presentation only: avoid source lookup racing the stop event.
# Cache synchronization, memory protection and checked suspension stay enabled.
configparams source-line-view 0
for {set i 0} {$i < 4} {incr i} {
 select_genesys_target "Cortex-A53 #$i"
 admit_core 1
}
# Reuse the qualified normal-runtime reset sequence BEFORE peripheral setup.
# Alternate JTAG prevents SD BootROM from restarting a competing runtime.
select_genesys_target PSU
mwr 0xFF5E0200 0x10E
select_genesys_target "Cortex-A53 #0"
rst -system
after 3000
puts "OCM_PS_SYSTEM_RESET_DONE"
# Do not suspend A53 while the cluster/L2 is still reset. Initialize clocks
# through PSU/DAP, then let AMD's processor-reset service activate CPU0.
select_genesys_target PSU
source $psu_init
# Reuse generated AMD MIO/clock/peripheral setup, explicitly exclude DDR.
init_ps [subst {$psu_mio_init_data $psu_peripherals_pre_init_data $psu_pll_init_data $psu_clock_init_data $psu_peripherals_init_data $psu_resetin_init_data $psu_resetout_init_data}]
init_peripheral
puts "PS_UART_CLOCK_INIT_DONE_NO_DDR"
select_genesys_target "Cortex-A53 #0"
rst -processor -stop -isa A64 -clear-registers
admit_core 0
for {set i 1} {$i < 4} {incr i} {
 select_genesys_target "Cortex-A53 #$i"
 admit_core 1
}
select_genesys_target "Cortex-A53 #0"
admit_core 0
dow $elf
con
puts "OCM_DIAGNOSTIC_STARTED"
disconnect
