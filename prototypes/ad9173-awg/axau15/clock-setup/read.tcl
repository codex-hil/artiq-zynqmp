source [file join [file dirname [info script]] transport.tcl]
# Fixed volatile profile only, host records every write. No HMC readback path.
proc dw {a v} {
 global dac_allowed
 if {![dict exists $dac_allowed $a] || $v ni [dict get $dac_allowed $a]} {error "DAC write outside clock profile"}
 transfer [expr {($a<<8)|$v}]
 puts [format "DAC_WRITE 0x%03x 0x%02x" $a $v]
}
proc hw {a v} {
 global hmc_allowed
 if {![dict exists $hmc_allowed $a] || $v ni [dict get $hmc_allowed $a]} {error "HMC write outside clock profile"}
 transfer [expr {($a<<8)|$v}] 1
 puts [format "HMC_WRITE_UNVERIFIED 0x%03x 0x%02x" $a $v]
}
set dac_allowed [dict create 0x3f {0} 0x100 {1} 0x90 {0} 0x91 {0} 0x95 {0} 0x790 {0} 0x791 {0} 0x796 {0xe5} 0x7a0 {0xbc} 0x794 {8} 0x797 {0x10 0x20} 0x798 {0x10} 0x7a2 {0x7f} 0x799 {5} 0x793 {0x18} 0x94 {1} 0x792 {2 0} 0xc0 {0} 0xdb {0 1} 0xc1 {0x68 0x69} 0xc7 {1}]
set hmc_profile {0x9f 0x4d 0xa0 0xdf 0xa5 6 0xa8 6 0xb0 4 5 0 3 0x0e 4 0x7f 0x33 1 0x34 0 0x35 12 0x36 0 0x32 0 0x5a 1 0x5c 0 0x5d 1 0xa 0 0xb 0 0xc 0 0xd 0 0xe 5 0xdd 12 0xde 0 0xdf 0 0xe0 0 0xe3 0 0xe4 3 0xdc 0x73}
set hmc_allowed [dict create 0 {1 0} 1 {2 0 0x80 0x40}]
foreach {a v} $hmc_profile {dict lappend hmc_allowed $a $v}
for {set ch 0} {$ch<14} {incr ch} {dict lappend hmc_allowed [expr {0xc8+10*$ch}] 0}
proc lockcheck {addr name} {
 set good 0
 for {set i 0} {$i<12} {incr i} {
  after 50
  set v [readreg $addr]
  if {$v&1} {incr good} else {set good 0}
  if {$good==3} {puts "LOCK_PASS $name";return}
 }
 error "$name did not lock (three consecutive samples required)"
}
$sq clear
$sq irshift -state IDLE -integer 6 3
$sq drshift -state IDLE -tdi 0 64
$sq run
gpio 12
set identified 0
set rc [catch {
 if {[readreg 4]!=0x72 || [readreg 5]!=0x91 || [readreg 3]!=4} {error "AD9172 identity mismatch; no initialization"}
 set identified 1
 dw 0x3f 0
 if {[readreg 0x3f]!=0} {error "TX disable readback failed"}
 if {![info exists ::env(ALINX_CLOCK_VERIFY_ONLY)]} {
 dw 0x100 1
 # HMC PLL1 disabled; VCXO free-running. Output2 alone drives DAC reference.
 hw 0 1;after 1;hw 0 0
 for {set ch 0} {$ch<14} {incr ch} {hw [expr {0xc8+10*$ch}] 0}
 foreach {a v} $hmc_profile {hw $a $v}
 hw 1 2;after 10;hw 1 0;hw 1 0x80;after 1;hw 1 0x40
 after 250
 puts "HMC_PROFILE_WRITTEN_NO_READBACK_OR_ID_CLAIM"
 foreach {a v} {0x90 0 0x91 0 0x95 0 0x790 0 0x791 0 0x796 0xe5 0x7a0 0xbc 0x794 8 0x797 0x10 0x797 0x20 0x798 0x10 0x7a2 0x7f} {dw $a $v}
 after 100
 foreach {a v} {0x799 5 0x793 0x18 0x94 1 0x792 2 0x792 0} {dw $a $v}
 after 100
 lockcheck 0x7b5 DAC_PLL
 foreach {a v} {0xc0 0 0xdb 0 0xdb 1 0xdb 0 0xc1 0x68 0xc1 0x69 0xc7 1} {dw $a $v}
 }
 lockcheck 0x7b5 DAC_PLL_FINAL
 lockcheck 0xc3 DAC_DLL
 foreach {a mask v} {0x799 0x3f 5 0x793 3 0 0x94 3 1 0x3f 0xff 0 0x100 1 1} {
  if {([readreg $a]&$mask)!=$v} {error "Clock/mute readback mismatch"}
 }
 puts "AD9172_CLOCK_PLL_DLL_PASS_NOMINAL_FS_4915200000_NO_RF"
} msg]
if {$identified} {catch {dw 0x3f 0}}
catch {gpio 12}
$sq clear
$sq irshift -state IDLE -integer 6 63
$sq run
disconnect
if {$rc} {error $msg}
