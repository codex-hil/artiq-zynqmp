source [file join [file dirname [info script]] transport.tcl]
set root [file dirname [info script]]
set f [open [file join $root tone-plan.tcl]];set plantext [read $f];close $f
set allowed [dict create 8 {1 8 64 128 192} 1430 {4 12} 63 {48} 768 {11 15}]
foreach line [split $plantext \n] {
 if {[regexp {^dw ([0-9]+) ([0-9]+)$} $line -> a v]} {dict lappend allowed $a $v}
}
proc dw {a v} {
 global allowed
 set a [expr {$a}];set v [expr {$v}]
 if {![dict exists $allowed $a] || $v ni [dict get $allowed $a]} {error "DAC write outside tone plan"}
 transfer [expr {($a<<8)|$v}]
 puts [format "DAC_WRITE 0x%03x 0x%02x" $a $v]
}
proc checkreg {a mask v} {
 if {([readreg $a]&$mask)!=$v} {error [format "DAC readback mismatch 0x%x" $a]}
}
proc scan {ir packet} {
 global sq
 $sq clear;$sq irshift -state IDLE -integer 6 $ir
 $sq drshift -state IDLE -capture -integer 64 $packet
 set h [lindex [$sq run -hex] 0]
 binary scan [binary format H* $h] i2 w
 return $w
}
proc phy {} {
 for {set i 0} {$i<3} {incr i} {set w [scan 2 0]}
 if {[lindex $w 1]!=0x41585031 || ([lindex $w 0]&511)!=511} {error "Payload image/PHY/link not ready"}
}
proc payload {v} {
 # A read packet has no write magic, so Capture/Update cannot retrigger writes.
 for {set i 0} {$i<3} {incr i} {set w [scan 34 0]}
 if {[lindex $w 1]!=0x41585062 || ([lindex $w 0]&65536)} {error "Payload signature or busy"}
 scan 34 [expr {(0x41585060<<32)|$v}]
 for {set i 0} {$i<30} {incr i} {
  after 10;set w [scan 34 0]
  if {[lindex $w 1]!=0x41585062} {error "Payload signature lost"}
  if {([lindex $w 0]&131071)==$v} {puts [format "PAYLOAD_ACK 0x%04x" $v];return}
 }
 error "Payload destination acknowledgement timeout"
}
proc links {} {
 phy
 foreach page {11 15} {
  dw 768 $page
  foreach a {0x470 0x471 0x472 0x473} {checkreg $a 3 3}
  foreach a {0x46d 0x46e 0x46f} {checkreg $a 3 0}
 }
 dw 768 11
 foreach a {0x7b5 0xc3 0x281} {checkreg $a 1 1}
}
scan 3 0;gpio 12
set identified 0
set rc [catch {
 phy
 checkreg 4 255 0x72;checkreg 5 255 0x91;checkreg 3 255 4
 set identified 1
 dw 8 192;dw 1430 4;dw 63 48
 payload 0
 links
 checkreg 0x110 255 0x23;checkreg 0x111 255 0x82
 foreach page {64 128} {
  dw 8 $page;checkreg 0x1e6 255 0;checkreg 0x112 255 8;checkreg 1430 12 4
 }
 foreach page {1 8} {
  dw 8 $page;checkreg 0x130 255 0x40;checkreg 0x131 2 2
  foreach a {0x132 0x133 0x134 0x135 0x136 0x137} {checkreg $a 255 0}
 }
 dw 8 192
 source [file join $root tone-plan.tcl]
 dw 8 192;dw 1430 12
 foreach {label word} {baseline 0 full 32767 half 16384 zero 0 recovered 32767 asymmetric 23170 final 32767} {
  payload $word
  links
  after 300
  set f [open [file join $root stage-$label.ready] w];puts $f $word;close $f
  set done 0
  for {set i 0} {$i<300} {incr i} {
   if {[file exists [file join $root abort]]} {error "Host measurement aborted"}
   if {[file exists [file join $root stage-$label.done]]} {set done 1;break}
   after 100
  }
  if {!$done} {error "Scope acknowledgement timeout"}
 }
 links
 dw 8 192;checkreg 1430 12 12
 puts "PHYSICAL_PAYLOAD_SEQUENCE_COMPLETE_HOST_RF_ACCEPTANCE_REQUIRED"
} msg]
if {$rc && $identified} {catch {payload 0};catch {dw 8 192};catch {dw 1430 4}}
catch {gpio 12}
$sq clear;$sq irshift -state IDLE -integer 6 63;$sq run
disconnect
if {$rc} {error $msg}
