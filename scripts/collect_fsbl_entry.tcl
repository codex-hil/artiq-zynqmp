# SPDX-License-Identifier: LGPL-3.0-or-later
# Library only: no connect, target selection, reset, download or execution.
# Parent must hold Genesys lease and select CPU0. Missing register names fail.
namespace eval fsbl_entry {
    proc selected_halted {} {
        set rows [targets -target-properties -filter {is_current == 1}]
        if {[llength $rows] != 1} {error "Nonunique current target"}
        set p [lindex $rows 0]
        foreach key {name jtag_cable_serial suspended} {
            if {![dict exists $p $key]} {error "Missing target property $key"}
        }
        if {[dict get $p name] ne "Cortex-A53 #0" ||
            [dict get $p jtag_cable_serial] ne "210383B7F02DA" ||
            ![dict get $p suspended]} {error "Wrong target or CPU not halted"}
    }
    proc register {name} {
        set path $name
        if {$name eq "sctlr_el3"} {set path {sys 1 sctlr_el3}}
        if {$name eq "mpidr_el1"} {set path {sys 0 mpidr_el1}}
        if {[regexp {^x([0-9]+)$} $name -> index]} {
            if {$index > 30} {error "Unsupported GP register"}
            set path [list r$index]
        }
        set leaf [lindex $path end]
        set pairs [rrd -nvlist {*}$path]
        if {[llength $pairs] != 2 || [lindex $pairs 0] ne $leaf} {
            error "Unexpected register response for $name"
        }
        set value [lindex $pairs 1]
        # XSDB nvlist returns hexadecimal strings, not decimal Tcl integers.
        if {![regexp {^(?:0x)?([0-9a-fA-F]{1,16})$} $value -> digits]} {
            error "Malformed register $name"
        }
        return [expr 0x$digits]
    }
    proc read_state {terminal} {
        selected_halted
        set pc [register pc]
        set pstate [register cpsr]
        if {$pstate > 0xffffffff || ($pstate & 31) ni {12 13}} {error "Expected live AArch64 EL3 PSTATE"}
        set el [expr {$pstate & 12}]
        if {$pc != $terminal && $pc != $terminal+4} {error "Outside FSBL terminal loop"}
        if {$el != 12} {error "Expected EL3 before privileged reads"}
        set ctl [register sctlr_el3]
        set masks [expr {$pstate & 0x3c0}]
        set affinity [register mpidr_el1]
        selected_halted
        return [dict create pc $pc currentel $el sctlr_el3 $ctl daif $masks mpidr_el1 $affinity cpsr $pstate]
    }
    proc sample {terminal} {
        set s [read_state $terminal]
        if {([dict get $s sctlr_el3] & 0x1005) != 0 ||
            [dict get $s daif] != 0x3c0 || ([dict get $s mpidr_el1] & 0xff) != 0} {
            error "Entry controls not admitted"
        }
        return $s
    }
    proc observe_pair {terminal} {
        set first [read_state $terminal]
        after 20
        set second [read_state $terminal]
        if {$first ne $second} {error "Observed state changed"}
        return [list $first $second]
    }
    proc collect {terminal} {
        if {![string is entier -strict $terminal] || $terminal < 0xfffc0000 ||
            $terminal > 0xfffffff4 || ($terminal & 3)} {error "Invalid OCM terminal"}
        set first [sample $terminal]
        after 20
        set second [sample $terminal]
        if {$first ne $second} {error "Stopped-state observation changed"}
        return [list $first $second]
    }
}
