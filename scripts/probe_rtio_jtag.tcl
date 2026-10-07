# Usage: xsdb probe_rtio_jtag.tcl SERVER_URL PSU_INIT_TCL CABLE_SERIAL
if {[llength $argv] != 3} {error "Require SERVER_URL PSU_INIT_TCL CABLE_SERIAL"}
lassign $argv server psu_init cable_serial
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
source $psu_init
# Configure only PL clock and AXI/reset; preserve trained DDR.
mask_write 0xFF5E00C0 0x013F3F07 0x01010C00
init_ps [subst {$psu_afi_config}]
psu_ps_pl_isolation_removal
psu_ps_pl_reset_config
configparams force-mem-accesses 1
mwr 0xA0000000 0x102
set target [mrd -value 0xA0000000]
if {$target != 0x102} {error "CSR readback mismatch $target"}
puts "TEST ps_pl PASS target=$target"
proc counter {} {
 mwr 0xA0000070 1
 set hi [mrd -value 0xA0000068]
 set lo [mrd -value 0xA000006C]
 return [expr {(wide($hi) << 32) | $lo}]
}
set before [counter]
after 1000
set after_value [counter]
if {$after_value <= $before} {error "RTIO counter is stopped"}
puts "TEST rtio_counter PASS before=$before after=$after_value delta=[expr {$after_value-$before}]"
puts "PL_CLOCK_CTRL=[mrd 0xFF5E00C0]"
# Schedule an output pulse; inspect internal PHY probe, not physical pin.
mwr 0xA0000800 1
mwr 0xA0000804 1
set now [counter]
set rise [expr {$now + 250000000}]
set fall [expr {$rise + 250000000}]
proc event {ts data} {
 mwr 0xA0000000 0
 mwr 0xA0000004 [expr {($ts >> 32) & 0xFFFFFFFF}]
 mwr 0xA0000008 [expr {$ts & 0xFFFFFFFF}]
 mwr 0xA0000048 $data
 set status [mrd -value 0xA000004C]
 if {$status != 0} {error "RTIO output status $status"}
}
event $rise 1
event $fall 0
mwr 0xA0001000 0
mwr 0xA0001004 0
after 2500
mwr 0xA0001008 1
set high [mrd -value 0xA000100C]
after 2000
mwr 0xA0001008 1
set low [mrd -value 0xA000100C]
if {$high != 1 || $low != 0} {error "Internal TTL probe failed high=$high low=$low"}
puts "TEST ttl_internal_probe PASS high=$high low=$low"
set errors [mrd -value 0xA000080C]
if {$errors != 0} {error "RTIO asynchronous errors $errors"}
puts "TEST rtio_async_errors PASS value=$errors"
puts "TEST ttl_physical NOT_RUN requires JB1-JB2 jumper or external instrument"
disconnect
