connect -url tcp:localhost:3121
set ms [jtag targets -target-properties -filter {jtag_cable_serial == "210512180081" && name == "xcau15p"}]
if {[llength $ms]!=1} {error "AXAU15 cable/part mismatch"}
set p [lindex $ms 0]
if {[string tolower [dict get $p idcode]] ne "04ac2093"} {error "IDCODE mismatch"}
jtag targets [dict get $p node_id]
set sq [jtag sequence]
proc gpio {pins} {
 global sq
 $sq clear
 $sq irshift -state IDLE -integer 6 3
 set packet [expr {(0x41534760 << 32) | $pins}]
 $sq drshift -state IDLE -capture -integer 64 $packet
 set h [lindex [$sq run -hex] 0]
 binary scan [binary format H* $h] i2 w
 if {[lindex $w 1]!=0x41534762} {error "SPI probe signature mismatch: $h"}
 if {[lindex $w 0]&32} {error "PIC owns FMC SPI; no DAC transactions permitted"}
 return [expr {([lindex $w 0]>>4)&1}]
}
proc transfer {command {target 0}} {
 set active [expr {$target==0?8:4}]
 set result 0
 gpio 12
 gpio $active
 for {set bit 23} {$bit>=0} {incr bit -1} {
  set pins [expr {$active|((($command>>$bit)&1)<<1)}]
  gpio $pins
  gpio [expr {$pins|1}]
  set value [gpio [expr {$pins|1}]]
  set result [expr {(($result<<1)|$value)&255}]
 }
 gpio $active
 gpio 12
 return $result
}
proc readreg {a} {
 set v [transfer [expr {0x800000|($a<<8)}]]
 puts [format "DAC_READ 0x%03x 0x%02x" $a $v]
 return $v
}
