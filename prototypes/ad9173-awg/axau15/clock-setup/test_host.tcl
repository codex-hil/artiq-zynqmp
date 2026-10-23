# Offline SPI slave model executes the actual host script. No hardware access.
array set regs {0 0 3 4 4 114 5 145 6 2 10 37 195 0 1973 0 641 0}
set gp 12;set mi 0;set n 0;set cmd 0;set packet 0;set readword 0
set writes {}
set cold [expr {[llength $argv]>0 && [lindex $argv 0] eq "cold"}]
if {$cold} {set regs(4) 0;set regs(5) 0}
proc connect {args} {}
proc disconnect {} {}
proc jtag {sub args} {
 if {$sub eq "sequence"} {return seq}
 if {[llength $args]>1} {return [list [dict create idcode 04ac2093 node_id 1]]}
}
proc seq {sub args} {
 global packet gp mi n cmd readword regs writes
 switch $sub {
 clear {set packet 0}
 drshift {
  set i [lsearch $args -integer]
  if {$i>=0} {set packet [lindex $args [expr {$i+2}]]}
 }
 run {
  set status [expr {$gp|($mi<<4)}]
  set h [binary encode hex [binary format i2 [list $status 0x41534762]]]
  if {($packet>>32)==0x41534760} {
   set new [expr {$packet&15}]
   if {($gp&12)==12 && ($new&12)!=12} {set n 0;set cmd 0;set mi 0}
   if {($new&12)!=12} {
    if {!($gp&1) && ($new&1)} {
     set cmd [expr {(($cmd<<1)|(($new>>1)&1))&0xffffff}];incr n
     if {$n==16} {
      set addr [expr {$cmd&0x7fff}]
      set readword [expr {[info exists regs($addr)]?$regs($addr):0}]
     }
     if {$n==24 && !($cmd&0x800000)} {
      set addr [expr {($cmd>>8)&0x7fff}];set v [expr {$cmd&255}]
      if {($new&4)==0} {
       set regs($addr) $v;lappend writes [list dac $addr $v]
       if {$addr==0x94} {set regs($addr) [expr {$v|16}]}
       if {$addr==0x792 && $v==0 && !$::unlock} {set regs(1973) 3}
       if {$addr==0xc7 && $v==1 && !$::unlock} {set regs(195) 1}
      } else {set ::hmc($addr) $v;lappend writes [list hmc $addr $v]}
     }
    }
    if {($gp&1) && !($new&1) && $n>=16 && $n<24} {set mi [expr {($readword>>(23-$n))&1}]}
   }
   set gp $new
  }
  return [list $h]
 }
 }
}

set unlock [expr {[llength $argv] && [lindex $argv 0] eq "unlock"}]
set wrongid [expr {[llength $argv] && [lindex $argv 0] eq "wrong-id"}]
if {$wrongid} {set regs(4) 115}
rename after real_after
proc after {args} {}
set rc [catch {source [file join [file dirname [info script]] read.tcl]} msg]
if {$gp!=12} {error "Chip selects not idle"}
if {$wrongid} {
 if {!$rc || [llength $writes]} {error "Wrong-ID guard failed"}
 puts "MODEL_WRONG_ID_NO_WRITES_PASS";exit
}
if {$regs(63)!=0} {error "TX not muted"}
if {$unlock} {
 if {!$rc || [string first "did not lock" $msg]<0} {error "Lock-negative guard failed"}
 puts "MODEL_UNLOCK_ABORT_MUTED_PASS";exit
}
if {$rc} {error $msg}
for {set ch 0} {$ch<14} {incr ch} {
 set a [expr {0xc8+10*$ch}]
 if {$hmc($a)!=[expr {$ch==2?0x73:0}]} {error "Unexpected HMC output enabled"}
}
if {$regs(1945)!=5 || $regs(1939)!=24 || $regs(148)!=17} {error "Wrong DAC clock plan"}
puts "MODEL_CLOCK_PROFILE_PASS_ONLY_OUTPUT2_DAC_MUTED"
