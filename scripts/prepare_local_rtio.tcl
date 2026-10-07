# Usage: xsdb prepare_local_rtio.tcl SERVER_URL PSU_INIT_TCL CABLE_SERIAL
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
# Preflight the actual PL window before permitting A53 accesses.
mwr 0xA0000070 1
puts "RTIO_COUNTER_HI=[mrd -value 0xA0000068]"
puts "RTIO_COUNTER_LO=[mrd -value 0xA000006C]"
puts "TEST pl_preflight PASS"
disconnect
