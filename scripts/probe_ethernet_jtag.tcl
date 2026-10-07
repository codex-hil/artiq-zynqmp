# Usage: xsdb probe_ethernet_jtag.tcl SERVER_URL CABLE_SERIAL
if {[llength $argv] != 2} {error "Require SERVER_URL CABLE_SERIAL"}
lassign $argv server cable_serial
proc select_genesys_target {name} {
    global cable_serial
    set matches {}
    foreach properties [targets -target-properties -filter "name == \"$name\""] {
        if {[dict exists $properties jtag_cable_serial] && [dict get $properties jtag_cable_serial] eq $cable_serial} {
            lappend matches [dict get $properties target_id]
        }
    }
    if {[llength $matches] != 1} {error "Target $name on $cable_serial not uniquely identified"}
    targets -set [lindex $matches 0]
}
connect -url $server
for {set i 0} {$i < 4} {incr i} {select_genesys_target "Cortex-A53 #$i"; catch {stop}}
select_genesys_target PSU
set control [mrd -value 0xFF0B0000]
set config [mrd -value 0xFF0B0004]
mwr 0xFF0B0000 [expr {$control | 0x10}]
mwr 0xFF0B0004 [expr {($config & ~0x1C0000) | 0x1C0000}]
proc mdio_read {phy reg} {
 mwr 0xFF0B0034 [expr {0x60020000 | ($phy << 23) | ($reg << 18)}]
 for {set n 0} {$n < 100} {incr n} {
  if {[mrd -value 0xFF0B0008] & 4} {return [expr {[mrd -value 0xFF0B0034] & 0xFFFF}]}
  after 1
 }
 error "MDIO timeout"
}
set found 0
for {set phy 0} {$phy < 32} {incr phy} {
 set id1 [mdio_read $phy 2]
 set id2 [mdio_read $phy 3]
 if {$id1 != 0 && $id1 != 65535} {
  incr found
  mdio_read $phy 1
  set status [mdio_read $phy 1]
  puts [format "PHY addr=%d id=%04X%04X BMSR=%04X link=%d autoneg_done=%d" $phy $id1 $id2 $status [expr {($status & 4)!=0}] [expr {($status & 32)!=0}]]
 }
}
mwr 0xFF0B0000 $control
mwr 0xFF0B0004 $config
if {$found == 0} {error "No Ethernet PHY found on GEM0 MDIO"}
puts "TEST ethernet_mdio PASS found=$found; packet TX/RX NOT_RUN"
disconnect
