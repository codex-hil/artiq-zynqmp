# Read-only CPU1 terminal-event observation; LGPL-3.0-or-later.
# Caller holds shared Genesys lease and restores immediately afterwards.
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
set ready 0
for {set retry 0} {$retry < 20} {incr retry} {
 set sequence [mrd -address-space AP0 -value 0x200FF040]
 set status [mrd -address-space AP0 -value 0x200FF044]
 if {$status == 7} {set ready 1; break}
 after 50
}
if {!$ready} {error "CPU1 terminal event not observed"}
set command [mrd -address-space AP0 -value 0x200FF004]
set length [mrd -address-space AP0 -value 0x200FF048]
if {$command != 5 || $length != 25} {error "Unexpected cancel command/event length"}
set message ""
for {set offset 0} {$offset < $length} {incr offset 4} {
 set word [mrd -address-space AP0 -value [expr {0x200FF100+$offset}]]
 for {set j 0} {$j < 4 && $offset+$j < $length} {incr j} {
  append message [format %c [expr {($word >> (8*$j)) & 255}]]
 }
}
set final_sequence [mrd -address-space AP0 -value 0x200FF040]
set final_status [mrd -address-space AP0 -value 0x200FF044]
if {$final_sequence != $sequence || $final_status != 7 || $message ne "RPC reply command invalid"} {
 error "Unstable or unexpected CPU1 terminal event"
}
puts "RPC_FAILSTOP command=$command status=$status sequence=$sequence message=$message"
puts "TEST rpc_cancel_terminal_event PASS"
puts "LIMIT clean_unwind_DMA_RTIO_quiescence_and_worker_reuse_NOT_PROVEN"
disconnect
