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
 set packet [expr {(0x41534750 << 32) | $pins}]
 $sq drshift -state IDLE -capture -integer 64 $packet
 set h [lindex [$sq run -hex] 0]
 binary scan [binary format H* $h] i2 w
 if {[lindex $w 1]!=0x41534752} {error "SPI probe signature mismatch: $h"}
 if {[lindex $w 0]&32} {error "PIC owns FMC SPI; no DAC transactions permitted"}
 return [expr {([lindex $w 0]>>4)&1}]
}
proc transfer {command} {
 set result 0
 gpio 4
 gpio 0
 for {set bit 23} {$bit>=0} {incr bit -1} {
  set pins [expr {(($command>>$bit)&1)<<1}]
  gpio $pins
  gpio [expr {$pins|1}]
  set value [gpio [expr {$pins|1}]]
  set result [expr {(($result<<1)|$value)&255}]
 }
 gpio 0
 gpio 4
 return $result
}
proc readreg {a} {
 set v [transfer [expr {0x800000|($a<<8)}]]
 puts [format "DAC_READ 0x%03x 0x%02x" $a $v]
 return $v
}
proc writereg {a v} {
 # Narrow volatile startup/scratch allowlist; no RF or nonvolatile programming.
 if {!($a==0 && $v in {0x18 0x81 0x3c}) && !($a==0x091 && $v==0) && !($a in {0x206 0x705} && $v==1) && $a!=0x00a} {error "Write not allowed"}
 transfer [expr {($a<<8)|$v}]
 puts [format "DAC_WRITE 0x%03x 0x%02x" $a $v]
}
# Run a no-command scan first to settle ownership synchronizer.
$sq clear
$sq irshift -state IDLE -integer 6 3
$sq drshift -state IDLE -tdi 0 64
$sq run
gpio 4
set rc [catch {
 foreach a {0 3 4 5 6} {readreg $a}
 # Datasheet SPI_INTFCONFA SDOACTIVE and mirror. No soft-reset bits.
 writereg 0 0x18
 set intf [readreg 0]
 set chip [readreg 3]
 set lo [readreg 4]
 set hi [readreg 5]
 set rev [readreg 6]
 # AD9172 datasheet Rev C Table49: load factory trim into volatile state.
 # This enables the loader; it does NOT program nonvolatile memory.
 if {$intf==0x18 && $chip==4 && $lo==0 && $hi==0} {
  puts "COLD_FACTORY_LOADER_BEGIN"
  writereg 0 0x81
  after 10
  writereg 0 0x3c
  writereg 0x091 0
  writereg 0x206 1
  writereg 0x705 1
  after 10
  set loader [readreg 0x705]
  if {$loader&1} {error "Factory loader did not complete within bounded wait"}
  set intf [readreg 0]
  set chip [readreg 3]
  set lo [readreg 4]
  set hi [readreg 5]
  set rev [readreg 6]
 }
 if {$intf ni {24 60} || $chip!=4 || $lo!=0x72 || $hi!=0x91} {
  error [format "AD9172 identity not established: intf=%02x chip=%02x id=%02x%02x" $intf $chip $hi $lo]
 }
 puts "AD9172_PHYSICAL_ID_PASS"
 set saved [readreg 0xa]
 set sr [catch {
  foreach pattern {0xa5 0x5a} {
   writereg 0xa $pattern
   if {[readreg 0xa]!=$pattern} {error "Scratch readback mismatch"}
  }
 } sm]
 writereg 0xa $saved
 if {[readreg 0xa]!=$saved} {error "Scratch restore failed"}
 if {$sr} {error $sm}
 puts "AD9172_SCRATCH_RESTORE_PASS"
 foreach a {0x0c3 0x7b5 0x281} {readreg $a}
} msg]
catch {gpio 4}
$sq clear
$sq irshift -state IDLE -integer 6 63
$sq run
disconnect
if {$rc} {error $msg}
puts "AD9172_SPI_PROBE_PASS_NO_RF_CLAIM"
