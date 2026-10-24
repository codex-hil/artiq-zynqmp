# Abstract SPI/JTAG model executes actual read.tcl; no physical access.
set scenario [lindex $argv 0]
array set regs {3 4 4 114 5 145 1973 3 195 1 1945 5 641 1}
if {$scenario eq "wrong-id"} {set regs(4) 115}
set writes {};set hmcwrites {};set sq seq
proc connect {args} {};proc disconnect {} {};proc gpio {args} {}
proc seq {sub args} {
 if {$sub eq "run"} {
  set status [expr {$::scenario eq "phy-timeout"?0:511}]
  return [list [binary encode hex [binary format i2 [list $status 0x41584a31]]]]
 }
}
proc transfer {command {target 0}} {
 set a [expr {($command>>8)&0x7fff}];set v [expr {$command&255}]
 if {$target} {lappend ::hmcwrites [list $a $v];return 0}
 if {$command&0x800000} {return [readreg $a]}
 set ::regs($a) $v;lappend ::writes [list $a $v]
 if {$a==0x131 && $v==1} {set ::regs($a) 3}
 return 0
}
proc readreg {a} {
 set a [expr {$a}]
 if {$a>=0x470 && $a<=0x473} {return [expr {$::scenario eq "bad-link" || ($::regs(768)&3)!=3 ? 0 : 3}]}
 if {$a>=0x46d && $a<=0x46f} {return 0}
 return [expr {[info exists ::regs($a)]?$::regs($a):0}]
}
rename source original_source
proc source {p} {if {[file tail $p] ne "transport.tcl"} {uplevel 1 [list original_source $p]}}
rename after original_after;proc after {args} {}
set rc [catch {source [file join [file dirname [info script]] read.tcl]} msg]
if {$scenario eq "wrong-id"} {
 if {!$rc || [llength $writes] || [llength $hmcwrites]} {error "Wrong ID wrote registers"}
} elseif {$scenario in {phy-timeout bad-link}} {
 if {!$rc || $regs(1430)!=4 || $regs(256)!=1 || [lindex $hmcwrites end] ne {320 0}} {error "Failure did not mute/disable"}
} else {
 if {$rc} {error $msg}
 if {$regs(1430)!=4 || $regs(63)!=48 || $regs(768)!=11} {error "Final mute/link state wrong"}
 foreach w $hmcwrites {if {[lindex $w 0]<0x140 || [lindex $w 0]>0x148} {error "Global HMC write"}}
}
puts "SIMULATION_ONLY HOST_PLAN $scenario PASS"
