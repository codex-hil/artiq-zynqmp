source [file join [file dirname [info script]] transport.tcl]
proc hw {a v} {
 set allowed [dict create 0x140 {0 0x73} 0x141 {12} 0x142 {0} 0x143 {0} 0x144 {0} 0x145 {0} 0x146 {0} 0x147 {0} 0x148 {0x10}]
 if {![dict exists $allowed $a] || $v ni [dict get $allowed $a]} {error "HMC write outside bounded LVDS profile"}
 transfer [expr {($a<<8)|$v}] 1
 puts [format "HMC_WRITE_UNVERIFIED 0x%03x 0x%02x" $a $v]
}
proc sample {} {
 global sq
 $sq clear
 $sq irshift -state IDLE -integer 6 2
 $sq drshift -state IDLE -capture -tdi 0 64
 set h [lindex [$sq run -hex] 0]
 binary scan [binary format H* $h] i2 w
 if {([lindex $w 1]&0xfffffffe)!=0x41585130} {error "QPLL image signature mismatch"}
 set n [expr {[lindex $w 0]&0xffffffff}]
 for {set s 1} {$s<32} {set s [expr {$s*2}]} {set n [expr {$n^($n>>$s)}]}
 return [list $n [expr {[lindex $w 1]&1}]]
}
proc check {enabled label} {
 after 100
 sample;sample
 lassign [sample] prev locked
 for {set i 0} {$i<3} {incr i} {
  after 100
  sample;sample
  lassign [sample] n locked
  set delta [expr {($n-$prev)&0xffffffff}]
  puts "PHYSICAL_QPLL $label SAMPLE=$i COUNT=$n DELTA=$delta LOCK=$locked"
  if {$enabled && (!$locked || $delta<1000000 || $delta>100000000)} {error "Reference activity or QPLL lock failed"}
  if {!$enabled && $delta!=0} {error "Reference counter advanced with HMC output12 disabled"}
  set prev $n
 }
}
$sq clear
$sq irshift -state IDLE -integer 6 3
$sq drshift -state IDLE -tdi 0 64
$sq run
gpio 12
set identified 0
set rc [catch {
 sample;sample
 if {[readreg 4]!=0x72 || [readreg 5]!=0x91 || [readreg 3]!=4} {error "AD9172 identity mismatch"}
 set identified 1
 transfer [expr {0x3f<<8}]
 if {[readreg 0x3f]!=0 || ([readreg 0x100]&1)!=1} {error "DAC mute/powerdown baseline mismatch"}
 if {([readreg 0x7b5]&1)!=1 || ([readreg 0xc3]&1)!=1} {error "DAC clock baseline unlocked"}
 hw 0x140 0
 check 0 BASELINE_OFF
 foreach {a v} {0x141 12 0x142 0 0x143 0 0x144 0 0x145 0 0x146 0 0x147 0 0x148 0x10} {hw $a $v}
 hw 0x140 0x73
 # Do not restart global HMC dividers: preserve the established DAC reference.
 check 1 LVDS_ON
 hw 0x140 0
 check 0 LOSS
 hw 0x140 0x73
 check 1 RECOVERY
 hw 0x140 0
 check 0 FINAL_OFF
 if {[readreg 0x3f]!=0 || ([readreg 0x7b5]&1)!=1 || ([readreg 0xc3]&1)!=1} {error "Final DAC mute/clock baseline failed"}
 puts "PHYSICAL_QPLL_LVDS_ACTIVITY_RECOVERY_PASS_NO_JESD_NO_ELECTRICAL_MEASUREMENT"
} msg]
if {$identified} {
 catch {hw 0x140 0}
 catch {transfer [expr {0x3f<<8}]}
}
catch {gpio 12}
$sq clear
$sq irshift -state IDLE -integer 6 63
$sq run
disconnect
if {$rc} {error $msg}
