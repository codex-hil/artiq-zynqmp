# Bounded read-only DDRC configuration inventory; LGPL-3.0-or-later.
# Caller must hold the shared Genesys lease. No CPU stop or writes.
if {[llength $argv] != 2} {error "Require SERVER_URL CABLE_SERIAL"}
lassign $argv server cable_serial
if {$cable_serial ne "210383B7F02DA"} {error "Wrong Genesys identity"}
connect -url $server
set matches {}
foreach properties [targets -target-properties -filter {name == "PSU"}] {
 if {[dict exists $properties jtag_cable_serial] && [dict get $properties jtag_cable_serial] eq $cable_serial} {
  lappend matches [dict get $properties target_id]
 }
}
if {[llength $matches] != 1} {error "Genesys PSU not unique"}
targets -set [lindex $matches 0]
configparams force-mem-accesses 1
foreach {name address} {
 MSTR 0xfd070000 ECCCFG0 0xfd070070
 ADDRMAP0 0xfd070200 ADDRMAP1 0xfd070204 ADDRMAP2 0xfd070208
 ADDRMAP3 0xfd07020c ADDRMAP4 0xfd070210 ADDRMAP5 0xfd070214
 ADDRMAP6 0xfd070218 ADDRMAP7 0xfd07021c ADDRMAP8 0xfd070220
 ADDRMAP9 0xfd070224 ADDRMAP10 0xfd070228 ADDRMAP11 0xfd07022c
} {
 set value [mrd -address-space AP0 -value $address]
 puts [format "DDR_CONFIG %s 0x%08x 0x%08x" $name $address $value]
}
puts "TEST ddr_config_snapshot PASS"
disconnect
