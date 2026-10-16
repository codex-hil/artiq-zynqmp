lassign $argv server cable
connect -url $server
set matches {}
foreach p [targets -target-properties -filter {name == "PSU"}] {
if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}
}
if {[llength $matches]!=1} {error "Exact Genesys target missing"}
targets -set [lindex $matches 0]
configparams force-mem-accesses 1
set addr(monitor_magic) 2684354560; set words(monitor_magic) 1
set addr(monitor_reset) 2684354564; set words(monitor_reset) 1
set addr(monitor_tx_enable) 2684354568; set words(monitor_tx_enable) 1
set addr(monitor_loopback) 2684354572; set words(monitor_loopback) 1
set addr(monitor_prbs) 2684354576; set words(monitor_prbs) 1
set addr(monitor_tx_prbs) 2684354580; set words(monitor_tx_prbs) 1
set addr(monitor_snapshot) 2684354584; set words(monitor_snapshot) 1
set addr(monitor_status) 2684354588; set words(monitor_status) 1
set addr(monitor_boot_ticks) 2684354592; set words(monitor_boot_ticks) 1
set addr(monitor_rx_ticks) 2684354596; set words(monitor_rx_ticks) 1
set addr(monitor_tx_ticks) 2684354600; set words(monitor_tx_ticks) 1
set addr(monitor_prbs_errors) 2684354604; set words(monitor_prbs_errors) 1
set addr(dma_address) 2684362752; set words(dma_address) 2
set addr(dma_time_offset) 2684362760; set words(dma_time_offset) 2
set addr(dma_max_bursts) 2684362768; set words(dma_max_bursts) 1
set addr(dma_watchdog) 2684362772; set words(dma_watchdog) 1
set addr(dma_start) 2684362776; set words(dma_start) 1
set addr(dma_abort) 2684362780; set words(dma_abort) 1
set addr(dma_clear) 2684362784; set words(dma_clear) 1
set addr(dma_active) 2684362788; set words(dma_active) 1
set addr(dma_pending) 2684362792; set words(dma_pending) 1
set addr(dma_reject) 2684362796; set words(dma_reject) 1
set addr(dma_result_error) 2684362800; set words(dma_result_error) 1
set addr(dma_result_channel) 2684362804; set words(dma_result_channel) 1
set addr(dma_result_timestamp) 2684362808; set words(dma_result_timestamp) 2
set addr(dma_accepted) 2684362816; set words(dma_accepted) 1
set addr(dma_completed) 2684362820; set words(dma_completed) 1
set addr(aux_aux_tx_length) 2684360704; set words(aux_aux_tx_length) 1
set addr(aux_aux_tx) 2684360708; set words(aux_aux_tx) 1
set addr(aux_aux_rx_present) 2684360712; set words(aux_aux_rx_present) 1
set addr(aux_aux_rx_error) 2684360716; set words(aux_aux_rx_error) 1
set addr(aux_aux_read_pointer) 2684360720; set words(aux_aux_read_pointer) 1
set addr(aux_bridge_busy) 2684360724; set words(aux_bridge_busy) 1
set addr(aux_rx_up) 2684360728; set words(aux_rx_up) 1
set addr(aux_in_reset) 2684360732; set words(aux_in_reset) 1
set addr(aux_tsc_load_count) 2684360736; set words(aux_tsc_load_count) 1
set addr(aux_rt_reply_fault) 2684360740; set words(aux_rt_reply_fault) 1
set addr(aux_rtio_error_flags) 2684360744; set words(aux_rtio_error_flags) 1
set addr(aux_rtio_spread_enable) 2684360748; set words(aux_rtio_spread_enable) 1
set addr(aux_rtio_reset_request) 2684360752; set words(aux_rtio_reset_request) 1
set addr(aux_rtio_reset_applied) 2684360756; set words(aux_rtio_reset_applied) 1
set addr(aux_phy_reset_request) 2684360760; set words(aux_phy_reset_request) 1
set addr(aux_phy_reset_applied) 2684360764; set words(aux_phy_reset_applied) 1
set addr(aux_tsc_snapshot_request) 2684360768; set words(aux_tsc_snapshot_request) 1
set addr(aux_tsc_snapshot_busy) 2684360772; set words(aux_tsc_snapshot_busy) 1
set addr(aux_tsc_snapshot_valid) 2684360776; set words(aux_tsc_snapshot_valid) 1
set addr(aux_tsc_snapshot_value) 2684360780; set words(aux_tsc_snapshot_value) 2
proc wr {name value} {
 global addr words
 for {set i 0} {$i<$words($name)} {incr i} {
  mwr [expr {$addr($name)+4*$i}] [expr {($value>>(32*($words($name)-1-$i)))&0xffffffff}]
 }
}
proc rd {name} {
 global addr words
 set value 0
 for {set i 0} {$i<$words($name)} {incr i} {
  set value [expr {($value<<32)|(wide([mrd -value [expr {$addr($name)+4*$i}]])&0xffffffff)}]
 }
 return $value
}
if {[rd monitor_magic]!=0x44525430} {error "Wrong PL identity"}
foreach n {aux_in_reset aux_rtio_reset_request aux_phy_reset_request aux_rt_reply_fault aux_rtio_error_flags dma_active} {
 if {[rd $n]!=0} {error "Unready DMA/RTIO: $n"}
}
if {[rd aux_rx_up]!=1 || [rd aux_tsc_load_count]==0} {error "No external TSC/link"}

proc binary_read {name} {
 set f [open $name rb];set data [read $f];close $f;return $data
}
proc snapshot {} {
 if {[rd aux_tsc_snapshot_busy]} {error "Snapshot already busy"}
 wr aux_tsc_snapshot_request 1
 set deadline [expr {[clock milliseconds]+1000}]
 while {[rd aux_tsc_snapshot_busy] || ![rd aux_tsc_snapshot_valid]} {
  if {[clock milliseconds]>$deadline} {error "Snapshot timeout"}
 }
 return [rd aux_tsc_snapshot_value]
}
set directory [file dirname [info script]]
set expected [binary_read [file join $directory trace.bin]]
if {[string length $expected]!=32768} {error "Wrong abort fixture size"}
mwr -bin -file [file join $directory trace.bin] 570425344 8192
mrd -bin -file [file join $directory readback.bin] 570425344 8192
if {[binary_read [file join $directory readback.bin]] ne $expected} {error "DDR block readback mismatch"}
wr dma_clear 1
set accepted [rd dma_accepted];set completed [rd dma_completed]
set epoch [rd aux_tsc_load_count]
wr dma_address 570425344
wr dma_time_offset 76029910816
wr dma_max_bursts 256
wr dma_watchdog 134217728
if {[rd dma_address]!=570425344 || [rd dma_max_bursts]!=256 || [rd dma_watchdog]!=134217728} {error "Abort configuration mismatch"}
set sampled_at [clock milliseconds]
set sampled [snapshot]
set offset 76029910816
if {[rd dma_time_offset]!=$offset} {error "Time offset readback mismatch"}
# Conservative age bound: at most2 mu/ns, plus1 second of lead.
if {$sampled+([clock milliseconds]-$sampled_at)*2000000+1000000000 >= $offset} {error "Insufficient future offset"}
wr dma_start 1
after 20
if {[rd dma_accepted]!=$accepted+1 || [rd dma_completed]!=$completed || ![rd dma_active] || [rd dma_pending]} {error "DMA did not remain active before abort"}
if {[rd dma_reject] || [rd dma_result_error]} {error "Unexpected preabort fault"}
puts "SATELLITE_DMA_PREABORT active=[rd dma_active] accepted=[rd dma_accepted] completed=[rd dma_completed] epoch=$epoch sampled=$sampled offset=$offset"
wr dma_abort 1
set deadline [expr {[clock milliseconds]+3000}]
while {[rd dma_active] || ![rd dma_pending]} {
 if {[clock milliseconds]>$deadline} {error "Abort/recovery timeout"}
 after 1
}
if {[rd dma_result_error]!=1 || [rd dma_reject] || [rd dma_accepted]!=$accepted+1 || [rd dma_completed]!=$completed+1} {error "Unexpected abort result"}
foreach n {aux_in_reset aux_rtio_reset_request aux_phy_reset_request aux_rtio_reset_applied aux_phy_reset_applied aux_rt_reply_fault aux_rtio_error_flags} {
 if {[rd $n]} {error "Postabort RTIO fault: $n"}
}
if {[rd aux_rx_up]!=1 || [rd aux_tsc_load_count]!=$epoch} {error "Postabort link/TSC epoch changed"}
if {[snapshot]<=$sampled} {error "TSC did not advance"}
if {$sampled+([clock milliseconds]-$sampled_at)*2000000+1000000000 >= $offset} {error "Abort too late for observation"}
# Keep sticky error/pending, do not clear/restart DMA or reset RTIO.
puts "SATELLITE_DMA_POSTABORT active=[rd dma_active] pending=[rd dma_pending] error=[rd dma_result_error] accepted=[rd dma_accepted] completed=[rd dma_completed] epoch=[rd aux_tsc_load_count]"
puts "SATELLITE_DMA_ABORT_DRAIN_PASS bytes=32768 bursts_limit=256 error=1"
disconnect
