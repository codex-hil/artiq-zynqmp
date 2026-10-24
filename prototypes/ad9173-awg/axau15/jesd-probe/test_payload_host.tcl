# Abstract host model only. RTL handshake has its own asynchronous-clock test.
set scenario [lindex $argv 0]
set sq seq;set writes {};set payloadword 0;set ir 0;set packet 0
array set regs {3 4 4 114 5 145 1973 3 195 1 641 3 768 11 272 35 273 130 274 8 304 64 305 3 1430 4 8 192}
if {$scenario eq "wrong-id"} {set regs(4) 115}
proc connect {args} {};proc disconnect {} {};proc gpio {args} {}
proc seq {sub args} {
 if {$sub eq "irshift"} {set ::ir [lindex $args end]}
 if {$sub eq "drshift"} {set ::packet [lindex $args end]}
 if {$sub eq "run"} {
  if {$::ir==2} {set w [list 511 0x41585031]} elseif {$::ir==34} {
   set w [list $::payloadword 0x41585062]
   if {($::packet>>32)==0x41585060} {set ::payloadword [expr {$::packet&65535}]}
  } else {set w [list 0 0]}
  return [list [binary encode hex [binary format i2 $w]]]
 }
}
proc readreg {a} {
 set a [expr {$a}]
 if {$a>=0x470 && $a<=0x473} {return [expr {($::regs(768)&3)==3?3:0}]}
 if {$a>=0x46d && $a<=0x46f} {return 0}
 if {$::scenario eq "nco-fail" && $a==0x113} {return 0}
 return [expr {[info exists ::regs($a)]?$::regs($a):0}]
}
proc transfer {command {target 0}} {
 if {$target} {error "Unexpected HMC write"}
 set a [expr {($command>>8)&32767}];set v [expr {$command&255}]
 if {$command&0x800000} {return [readreg $a]}
 set ::regs($a) [expr {$a==0x113 && $v==1?3:$v}]
 lappend ::writes [list $a $v]
}
rename source original_source
proc source {p} {if {[file tail $p] ne "transport.tcl"} {uplevel 1 [list original_source $p]}}
rename after original_after;proc after {args} {}
rename file original_file
proc file {sub args} {
 if {$sub eq "exists"} {
  if {[string match *.done [lindex $args 0]]} {return 1}
  if {[original_file tail [lindex $args 0]] eq "abort"} {return [expr {$::scenario eq "scope-abort"}]}
 }
 return [original_file $sub {*}$args]
}
rename open original_open
proc open {path args} {
 if {[string match *.ready $path]} {set path /dev/null}
 return [original_open $path {*}$args]
}
set rc [catch {source [file join [file dirname [info script]] payload.tcl]} msg]
if {$scenario eq "wrong-id"} {
 if {!$rc || [llength $writes] || $payloadword!=0} {error "Wrong ID changed hardware"}
} elseif {$scenario in {nco-fail scope-abort}} {
 if {!$rc || $regs(1430)!=4 || $payloadword!=0} {error "Failure did not mute"}
} else {
 if {$rc} {error $msg}
 if {$regs(1430)!=12 || $payloadword!=32767} {error "Final state wrong"}
}
puts "SIMULATION_ONLY PAYLOAD_HOST $scenario PASS"
