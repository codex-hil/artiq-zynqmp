# Management CSR operations; UART firmware uses I2C only, not PL.
# Usage: SERVER CABLE OP VALUE FORWARD_ADDR
if {[llength $argv]!=5} {error "Expected SERVER CABLE OP VALUE FORWARD_ADDR"}
lassign $argv server cable op value forward
if {$forward!=0xA0000030} {error "Unsupported clock-forward CSR map"}
connect -url $server
set matches {}
foreach p [targets -target-properties -filter {name == "PSU"}] {
 if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}
}
if {[llength $matches]!=1} {error "Exact Genesys cable not found"}
targets -set [lindex $matches 0]
configparams force-mem-accesses 1
if {[mrd -value 0xA0000000]!=0x44525430} {error "Wrong diagnostic map"}
switch -- $op {
 gate {
  if {$value!=0&&$value!=1} {error "Invalid gate value"}
  mwr $forward $value
  puts "CLOCK_GATE [mrd -value $forward]"
 }
 restart {
  mwr 0xA0000004 1
  mwr 0xA0000008 0
  mwr 0xA000000C 2
  mwr 0xA0000010 1
  mwr 0xA0000014 1
  after 100
  mwr 0xA0000004 0
  set deadline [expr {[clock milliseconds]+10000}]
  while {1} {
   mwr 0xA0000018 1
   set status [mrd -value 0xA000001C]
   if {($status & 0x7f)==0x7f} {break}
   if {[clock milliseconds]>$deadline} {error "GTH restart timeout"}
   after 50
  }
  after 1000
  puts "CLOCK_GTH_RESTART PASS"
 }
 source {
  if {$value!=0&&$value!=1} {error "Invalid source value"}
  mwr 0xA0000034 $value
  puts "CLOCK_SOURCE [mrd -value 0xA0000034]"
 }
 snapshot {
  mwr 0xA0000018 1
  puts "CLOCK_SNAPSHOT [mrd -value 0xA000001c] [mrd -value 0xA0000020] [mrd -value 0xA0000024] [mrd -value 0xA0000028] [mrd -value 0xA000002c]"
 }
 default {error "Unsupported operation"}
}
disconnect
