# SPDX-License-Identifier: LGPL-3.0-or-later
# Called only by inherited-lease Python child, after FSBL UART completion.
if {[llength $argv] ni {4 5}} {error "Require SERVER ELF TERMINAL CABLE"}
lassign $argv server elf terminal cable mode
if {$mode eq ""} {set mode observe}
if {$mode ni {observe definitions controls exception exception-brk}} {error "Unknown observer mode"}
if {$cable ne "210383B7F02DA"} {error "Wrong cable"}
source [file join [file dirname [info script]] collect_fsbl_entry.tcl]
proc select_cpu0 {} {
    set ids {}
    foreach p [targets -target-properties -filter {name == "Cortex-A53 #0"}] {
        if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq "210383B7F02DA"} {
            lappend ids [dict get $p target_id]
        }
    }
    if {[llength $ids] != 1} {error "CPU0 not uniquely identified"}
    targets -set [lindex $ids 0]
}
proc halt_checked {} {
    set p [lindex [targets -target-properties -filter {is_current == 1}] 0]
    if {![dict exists $p suspended]} {error "Missing suspension state"}
    if {![dict get $p suspended]} {stop}
    for {set i 0} {$i <= 20} {incr i} {
        set p [lindex [targets -target-properties -filter {is_current == 1}] 0]
        if {[dict exists $p suspended] && [dict get $p suspended]} {
            fsbl_entry::selected_halted
            return
        }
        if {$i < 20} {after 50}
    }
    error "CPU0 halt not confirmed"
}
connect -url $server
configparams source-line-view 0
select_cpu0
halt_checked
if {$mode in {exception exception-brk}} {
    source [file join [file dirname [info script]] load_el3_exception_observer.tcl]
    if {$mode eq "exception-brk"} {
        if {![catch {exception_observer::run $elf $terminal brk} message options]} {
            error "BRK probe unexpectedly returned normally"
        }
        if {[dict get $options -errorcode] ne {OBSERVER FAULT_CAPTURED}} {
            return -options $options $message
        }
        # Transport marker only; Python must verify exact BRK/vector/ELR/PSTATE.
        puts "EXPECTED_BRK_TRANSPORT_CAPTURED"
    } else {exception_observer::run $elf $terminal normal}
    disconnect
    return
}
if {$mode eq "definitions"} {
    set pc [fsbl_entry::register pc]
    if {$pc != $terminal && $pc != $terminal+4} {error "Outside FSBL terminal"}
    puts "FSBL_REGISTER_DEFINITIONS_BEGIN"
    puts [rrd -defs]
    puts "FSBL_REGISTER_DEFINITIONS_END"
    puts "FSBL_SYS_DEFINITIONS_BEGIN"
    puts [rrd -defs sys]
    puts "FSBL_SYS_DEFINITIONS_END"
    for {set group 0} {$group < 16} {incr group} {
        puts "FSBL_SYS_CHILD_BEGIN $group"
        puts [rrd -defs sys $group]
        puts "FSBL_SYS_CHILD_END $group"
    }
    puts "FSBL_CPSR_RAW [fsbl_entry::register cpsr]"
    fsbl_entry::selected_halted
    disconnect
    return
}
if {$mode eq "controls"} {
    foreach sample [fsbl_entry::observe_pair $terminal] {puts "FSBL_CONTROL_STATE $sample"}
    puts "FSBL_CONTROL_OBSERVATION_ONLY"
    disconnect
    return
}
set samples [fsbl_entry::collect $terminal]
foreach s $samples {puts "TRAINED_ENTRY $s"}
# No reset after training. Normal XSDB cache synchronization remains enabled.
dow $elf
fsbl_entry::selected_halted
if {[fsbl_entry::register pc] != 0xfffc0000} {error "Observer entry PC not selected by download"}
con
after 20
halt_checked
set pc [fsbl_entry::register pc]
if {$pc != 0xfffc0034} {error "Observer did not reach EL3 success terminal: $pc"}
foreach name {x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 x15} {
    puts "OBSERVER_REGISTER $name [fsbl_entry::register $name]"
}
puts "OBSERVER_PC $pc"
disconnect
