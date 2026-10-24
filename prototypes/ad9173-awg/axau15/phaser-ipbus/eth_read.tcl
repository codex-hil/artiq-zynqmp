source [file join [file dirname [info script]] transport.tcl]
proc ethgpio {pins} {
 global sq
 $sq clear;$sq irshift -state IDLE -integer 6 34
 $sq drshift -state IDLE -capture -integer 64 [expr {(0x41584560<<32)|$pins}]
 set h [lindex [$sq run -hex] 0]
 binary scan [binary format H* $h] i2 w
 if {[lindex $w 1]!=0x41584562} {error "Ethernet scan identity mismatch"}
 return [expr {[lindex $w 0]&511}]
}
proc bitout {v} {set p [expr {4|($v<<1)}];ethgpio $p;ethgpio [expr {$p|1}];ethgpio $p}
proc bitin {} {ethgpio 0;ethgpio 1;set v [ethgpio 1];ethgpio 0;return [expr {($v>>8)&1}]}
set phy_address 1
set last_ta 1
proc mdio_read {a {probe 0}} {
 global phy_address last_ta
 for {set i 0} {$i<32} {incr i} {bitout 1}
 foreach bit {0 1 1 0} {bitout $bit}
 for {set i 4} {$i>=0} {incr i -1} {bitout [expr {($phy_address>>$i)&1}]}
 for {set i 4} {$i>=0} {incr i -1} {bitout [expr {($a>>$i)&1}]}
 # Last address bit ends with a falling MDC edge. The released interval
 # supplies Z; the first sampled read clock is the driven-zero TA bit.
 set ta [bitin]
 set result 0
 for {set i 0} {$i<16} {incr i} {set result [expr {($result<<1)|[bitin]}]}
 bitin;ethgpio 0
 set last_ta $ta
 if {$ta!=0 && !$probe} {error "PHY MDIO turnaround missing at address$phy_address"}
 puts [format "PHY_MDIO_READ ADDRESS=%d REG=0x%02x VALUE=0x%04x TA=%d" $phy_address $a $result $ta]
 return $result
}
$sq clear;$sq irshift -state IDLE -integer 6 34;$sq drshift -state IDLE -tdi 0 64;$sq run
set rc [catch {
 puts [format "ETH_STATUS 0x%03x" [ethgpio 0]]
 foreach a {2 3 0 1 1 4 5 9 10 17} {mdio_read $a}
 set idhi [mdio_read 2];set idlo [mdio_read 3]
 if {$idhi!=0x937c || ($idlo&0xfff0)!=0x4030} {error "Unexpected PHY identity"}
 mdio_read 1;set link [mdio_read 1]
 if {($link&0x24)!=0x24 || ([mdio_read 10]&0x3800)!=0x3800} {error "Gigabit link not ready"}
 after 500
 puts [format "ETH_STATUS 0x%03x" [ethgpio 0]]
} msg]
catch {ethgpio 0}
$sq clear;$sq irshift -state IDLE -integer 6 63;$sq run
disconnect
if {$rc} {error $msg}
