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
        set pairs [rrd -nvlist $name]
        if {[llength $pairs] != 2 || [lindex $pairs 0] ne $name} {
            error "Unexpected register response for $name"
        }
        set value [lindex $pairs 1]
        # XSDB nvlist returns hexadecimal strings, not decimal Tcl integers.
        if {![regexp {^(?:0x)?([0-9a-fA-F]{1,16})$} $value -> digits]} {
            error "Malformed register $name"
        }
        return [expr 0x$digits]
    }
    proc sample {terminal} {
        selected_halted
        set pc [register pc]
        set el [register currentel]
        if {$pc != $terminal && $pc != $terminal+4} {error "Outside FSBL terminal loop"}
        if {$el != 12} {error "Expected EL3 before privileged reads"}
        set ctl [register sctlr_el3]
        set masks [register daif]
        set affinity [register mpidr_el1]
        if {($ctl & 0x1005) != 0 || ($masks & 0x3c0) != 0x3c0 ||
            ($affinity & 0xff) != 0} {error "Entry controls not admitted"}
        selected_halted
        return [dict create pc $pc currentel $el sctlr_el3 $ctl daif $masks mpidr_el1 $affinity]
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
