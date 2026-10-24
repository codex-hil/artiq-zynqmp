source [file join [file dirname [info script]] transport.tcl]
set plan [file join [file dirname [info script]] dac-plan.tcl]
set f [open $plan];set plantext [read $f];close $f
set allowed [dict create 768 {8 15} 256 {1}]
foreach line [split $plantext \n] {
 if {[regexp {^dw ([0-9]+) ([0-9]+)$} $line -> a v]} {dict lappend allowed $a $v}
}
proc dw {a v} {
 global allowed
 set a [expr {$a}];set v [expr {$v}]
 if {![dict exists $allowed $a] || $v ni [dict get $allowed $a]} {error "DAC write outside fixed JESD plan"}
 transfer [expr {($a<<8)|$v}]
 puts [format "DAC_WRITE 0x%03x 0x%02x" $a $v]
}
proc checkreg {a mask v} {
 if {([readreg $a]&$mask)!=$v} {error [format "DAC readback mismatch 0x%x" $a]}
}
proc hw {a v} {
 set allowed [dict create 0x140 {0 0x73} 0x141 {12} 0x142 {0} 0x143 {0} 0x144 {0} 0x145 {0} 0x146 {0} 0x147 {0} 0x148 {0x10}]
 if {![dict exists $allowed $a] || $v ni [dict get $allowed $a]} {error "HMC write outside channel12 profile"}
 transfer [expr {($a<<8)|$v}] 1
 puts [format "HMC_WRITE_UNVERIFIED 0x%03x 0x%02x" $a $v]
}
if {![info exists image_magic]} {set image_magic 0x41584a31}
proc fpga {} {
 global sq image_magic
 $sq clear
 $sq irshift -state IDLE -integer 6 2
 $sq drshift -state IDLE -capture -tdi 0 64
 set h [lindex [$sq run -hex] 0]
 binary scan [binary format H* $h] i2 w
 if {[lindex $w 1]!=$image_magic} {error "JESD image signature mismatch"}
 return [expr {[lindex $w 0]&511}]
}
proc waitfpga {mask} {
 for {set i 0} {$i<30} {incr i} {
  after 100;fpga;fpga;set v [fpga]
  puts [format "FPGA_JESD_STATUS 0x%03x REQUIRED 0x%03x" $v $mask]
  if {($v&$mask)==$mask} {return}
 }
 error "FPGA did not reach required status"
}
$sq clear
$sq irshift -state IDLE -integer 6 3
$sq drshift -state IDLE -tdi 0 64
$sq run
gpio 12
set identified 0
set rc [catch {
 fpga;fpga
 checkreg 4 255 0x72;checkreg 5 255 0x91;checkreg 3 255 4
 set identified 1
 # 0x3f selects muting behavior, not the TXEN value. Explicit SPI TXEN low.
 dw 8 192;dw 1430 4;dw 63 48
 checkreg 1430 12 4
 checkreg 0x7b5 1 1;checkreg 0xc3 1 1
 hw 0x140 0
 foreach {a v} {0x141 12 0x142 0 0x143 0 0x144 0 0x145 0 0x146 0 0x147 0 0x148 0x10} {hw $a $v}
 hw 0x140 0x73
 waitfpga 31
 source $plan
 waitfpga 511
 for {set rep 0} {$rep<3} {incr rep} {
  after 200
  foreach page {11 15} {
   dw 768 $page
   set ok 1
   foreach a {0x470 0x471 0x472 0x473 0x46d 0x46e 0x46f} {
    set v [readreg $a]
    puts [format "LINK_STATUS REP=%d PAGE=%d REG=0x%x VALUE=0x%x" $rep $page $a $v]
    if {$a>=0x470 && ($v&3)!=3} {set ok 0}
    if {$a<0x470 && ($v&3)!=0} {set ok 0}
   }
   if {!$ok} {error "DAC CGS/ILAS/data or error status failed"}
  }
 }
 dw 768 11
 checkreg 0x7b5 1 1;checkreg 0xc3 1 1;checkreg 0x281 1 1
 dw 8 192;checkreg 1430 12 4
 puts "PHYSICAL_JESD_CGS_ILAS_STATUS_PASS_ZERO_PAYLOAD_NO_RF_AMPLITUDE_PROOF"
} msg]
if {$identified} {
 catch {dw 8 192};catch {dw 1430 4}
 if {$rc} {catch {dw 768 8};catch {dw 256 1};catch {hw 0x140 0}}
}
catch {gpio 12}
$sq clear;$sq irshift -state IDLE -integer 6 63;$sq run
disconnect
if {$rc} {error $msg}
