# Offline SPI slave model executes the actual host script. No hardware access.
array set regs {0 0 3 4 4 114 5 145 6 2 10 37 195 0 1973 0 641 0}
set gp 4;set mi 0;set n 0;set cmd 0;set packet 0;set readword 0
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
  set h [binary encode hex [binary format i2 [list $status 0x41534752]]]
  if {($packet>>32)==0x41534750} {
   set new [expr {$packet&7}]
   if {($gp&4) && !($new&4)} {set n 0;set cmd 0;set mi 0}
   if {!($new&4)} {
    if {!($gp&1) && ($new&1)} {
     set cmd [expr {(($cmd<<1)|(($new>>1)&1))&0xffffff}];incr n
     if {$n==16} {
      set addr [expr {$cmd&0x7fff}]
      set readword [expr {[info exists regs($addr)]?$regs($addr):0}]
     }
     if {$n==24 && !($cmd&0x800000)} {
      set addr [expr {($cmd>>8)&0x7fff}];set v [expr {$cmd&255}]
      set regs($addr) $v;lappend writes [list $addr $v]
      if {$addr==0x705 && $v==1} {set regs(4) 114;set regs(5) 145;set regs(1797) 2}
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
set negative [expr {[llength $argv]>0 && [lindex $argv 0] eq "wrong-id"}]
if {$negative} {set regs(4) 115}
set rc [catch {source [file join [file dirname [info script]] read.tcl]} msg]
if {$negative} {
 if {!$rc || $writes ne {{0 24}} || $gp!=4} {error "Wrong-ID guard failed: $msg $writes"}
 puts "HOST_WRONG_ID_REJECTED_NO_SCRATCH_WRITES_PASS"
 exit 0
}
if {$rc} {error $msg}
if {$regs(10)!=37 || $gp!=4} {error "scratch or chip select not restored"}
set expected {{0 24} {10 165} {10 90} {10 37}}
if {$cold} {set expected {{0 24} {0 129} {0 60} {145 0} {518 1} {1797 1} {10 165} {10 90} {10 37}}}
if {$writes ne $expected} {error "Unexpected writes $writes"}
puts "HOST_SPI_MODEL_PASS_ID_SCRATCH_RESTORE_AND_EXACT_WRITE_ALLOWLIST"
