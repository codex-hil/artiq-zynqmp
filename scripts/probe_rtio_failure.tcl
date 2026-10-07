# Inspect fail-stop mailbox after the explicit underflow negative control.
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
configparams force-mem-accesses 1
set status [mrd -address-space AP0 -value 0x200FF044]
set length [mrd -address-space AP0 -value 0x200FF048]
if {$status != 7 || $length > 4096} {error "No valid worker failure event"}
set message ""
for {set offset 0} {$offset < $length} {incr offset 4} {
 set word [mrd -address-space AP0 -value [expr {0x200FF100+$offset}]]
 for {set j 0} {$j < 4 && $offset+$j < $length} {incr j} {
  append message [format %c [expr {($word >> (8*$j)) & 255}]]
 }
}
puts "WORKER_FAILURE=$message"
if {$message ne "RTIOUnderflow; restart CPU1 required"} {error "Unexpected failure reason"}
set output_status [mrd -address-space AP0 -value 0xA000004C]
puts "RTIO_O_STATUS=$output_status"
if {($output_status & 2) == 0} {error "PL did not report underflow"}
puts "TEST real_rtio_underflow_failstop PASS"
disconnect
