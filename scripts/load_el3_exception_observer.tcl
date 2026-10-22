# SPDX-License-Identifier: LGPL-3.0-or-later
# Library only. Parent owns lease, selected halted CPU0, checked ELF and FSBL.
source [file join [file dirname [info script]] collect_fsbl_entry.tcl]
namespace eval exception_observer {
    proc halt {} {
        stop
        for {set i 0} {$i <= 20} {incr i} {
            set rows [targets -target-properties -filter {is_current == 1}]
            if {[llength $rows] == 1 && [dict exists [lindex $rows 0] suspended] &&
                [dict get [lindex $rows 0] suspended]} {
                fsbl_entry::selected_halted
                return
            }
            if {$i < 20} {after 50}
        }
        error "Observer halt unconfirmed"
    }
    proc unchanged_controls {before} {
        fsbl_entry::selected_halted
        foreach {field register} {cpsr cpsr sctlr_el3 sctlr_el3 mpidr_el1 mpidr_el1} {
            if {[fsbl_entry::register $register] != [dict get $before $field]} {
                error "Control state changed: $field"
            }
        }
    }
    proc run {elf terminal mode} {
        if {$mode ni {normal brk}} {error "Invalid probe mode"}
        set samples [fsbl_entry::observe_pair $terminal]
        set before [lindex $samples 0]
        # Separate policy: leave A as observed; D/I/F must already be masked.
        # A may be clear ONLY because verified vectors are installed before con.
        if {([dict get $before cpsr] & 31) != 13 ||
            ([dict get $before sctlr_el3] & 0x1005) != 0 ||
            ([dict get $before daif] & 0x2c0) != 0x2c0 ||
            ([dict get $before mpidr_el1] & 255) != 0} {
            error "Exception-observer entry not admitted"
        }
        set old_vbar [fsbl_entry::register {sys 12 vbar_el3}]
        puts "EXCEPTION_ENTRY_STATE $before"
        puts "EXCEPTION_OLD_VBAR $old_vbar"
        dow $elf
        unchanged_controls $before
        if {[fsbl_entry::register pc] != 0xfffc8800} {error "Unexpected download entry"}
        rwr sys 12 vbar_el3 0xfffc8000
        for {set i 0} {$i < 2} {incr i} {
            if {[fsbl_entry::register {sys 12 vbar_el3}] != 0xfffc8000} {
                error "VBAR readback mismatch; must not continue"
            }
        }
        if {$mode eq "brk"} {rwr pc 0xfffc8840}
        set entry [expr {$mode eq "brk" ? 0xfffc8840 : 0xfffc8800}]
        if {[fsbl_entry::register pc] != $entry} {error "Probe PC mismatch"}
        unchanged_controls $before
        puts "EXCEPTION_ARMED_VBAR 4294737920"
        con
        # Observe backend resume state for a bounded 1s, rather than assuming
        # a 20ms host delay proves execution. Final register markers still decide.
        for {set tick 0} {$tick < 10} {incr tick} {
            after 100
            set rows [targets -target-properties -filter {is_current == 1}]
            if {[llength $rows] != 1} {error "Resume target not unique"}
            set state [lindex $rows 0]
            foreach key {name jtag_cable_serial suspended} {
                if {![dict exists $state $key]} {error "Missing resume state $key"}
            }
            if {[dict get $state name] ne "Cortex-A53 #0" ||
                [dict get $state jtag_cable_serial] ne "210383B7F02DA"} {
                error "Resume target identity changed"
            }
            puts "EXCEPTION_RESUME_STATE tick=$tick suspended=[dict get $state suspended]"
        }
        halt
        set pc [fsbl_entry::register pc]
        puts "EXCEPTION_STOP_PC $pc"
        foreach name {x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 x14 x15 x16 x17 x18 x19 x20 x21} {
            puts "EXCEPTION_REGISTER $name [fsbl_entry::register $name]"
        }
        if {$pc == 0xfffc8878} {
            error "EXCEPTION_CAPTURED: mandatory restoration, never normal observation PASS"
        }
        if {$mode ne "normal" || $pc != 0xfffc8834 || [fsbl_entry::register x15] != 0x33} {
            error "Unexpected observer outcome"
        }
        if {[fsbl_entry::register x0] != 12 || [fsbl_entry::register x9] != 0xfffc8800 ||
            [fsbl_entry::register x1] != [dict get $before sctlr_el3] ||
            [fsbl_entry::register x6] != [dict get $before daif]} {
            error "Observer snapshot changed entry state"
        }
        puts "EXCEPTION_OBSERVER_NORMAL_COMPLETE"
    }
}
