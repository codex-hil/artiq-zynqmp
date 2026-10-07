# Usage: xsdb probe_ethernet_counters_jtag.tcl SERVER_URL CABLE_SERIAL
# Read GEM counters without halting A53. Statistics registers are clear-on-read.
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
select_genesys_target PSU
set tx [mrd -value 0xFF0B0108]
set rx [mrd -value 0xFF0B0158]
puts "GEM_FRAMES tx=$tx rx=$rx"
foreach {name address} {tx_underrun 0xFF0B0134 rx_fcs 0xFF0B0190 rx_alignment 0xFF0B019C rx_resource 0xFF0B01A0} {
 set value [mrd -value $address]
 puts "GEM_ERROR $name=$value"
 if {$value != 0} {error "GEM error counter $name nonzero: $value"}
}
if {$tx == 0 || $rx == 0} {error "No error-free frames counted in both directions"}
puts "TEST ethernet_mac_counters PASS"
disconnect
