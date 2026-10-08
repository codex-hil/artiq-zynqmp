# Usage: xsdb prepare_ps.tcl SERVER PSU_INIT CABLE
if {[llength $argv] != 3} {error "Require SERVER PSU_INIT CABLE"}
lassign $argv server psu_init cable
connect -url $server
proc select_exact {name} {
 global cable
 set matches {}
 foreach p [targets -target-properties -filter "name == \"$name\""] {
  if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {
   lappend matches [dict get $p target_id]
  }
 }
 if {[llength $matches] != 1} {error "Target $name on $cable is not unique"}
 targets -set [lindex $matches 0]
}
for {set i 0} {$i < 4} {incr i} {select_exact "Cortex-A53 #$i"; catch {stop}}
select_exact PSU
source $psu_init
mask_write 0xFF5E00C0 0x013F3F07 0x01010C00
init_ps [subst {$psu_afi_config}]
psu_ps_pl_isolation_removal
psu_ps_pl_reset_config
configparams force-mem-accesses 1
set magic [mrd -value 0xA0000000]
if {$magic != 0x44525430} {error "Not the DRTIO diagnostic map: $magic"}
puts "TEST DRTIO_DIAGNOSTIC_PS_PL PASS magic=$magic"
disconnect
