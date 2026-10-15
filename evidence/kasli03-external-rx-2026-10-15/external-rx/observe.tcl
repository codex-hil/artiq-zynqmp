lassign $argv server cable
connect -url $server
set matches {}
foreach p [targets -target-properties -filter {name == "PSU"}] {
if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}
}
if {[llength $matches]!=1} {error "Exact Genesys target missing"}
targets -set [lindex $matches 0]
configparams force-mem-accesses 1
set addr(monitor_magic) 2684354560
set addr(monitor_reset) 2684354564
set addr(monitor_tx_enable) 2684354568
set addr(monitor_loopback) 2684354572
set addr(monitor_prbs) 2684354576
set addr(monitor_tx_prbs) 2684354580
set addr(monitor_snapshot) 2684354584
set addr(monitor_status) 2684354588
set addr(monitor_boot_ticks) 2684354592
set addr(monitor_rx_ticks) 2684354596
set addr(monitor_tx_ticks) 2684354600
set addr(monitor_prbs_errors) 2684354604
set addr(observer_enable) 2684360704
set addr(observer_alignment) 2684360708
set addr(observer_rt_words) 2684360712
set addr(observer_rt_frames) 2684360716
set addr(observer_aux_words) 2684360720
set addr(observer_aux_frames) 2684360724

proc wr {n v} {global addr; mwr $addr($n) $v}
proc rd {n} {global addr; return [expr {wide([mrd -value $addr($n)]) & 0xffffffff}]}
proc sample {} {
 wr monitor_snapshot 1
 set values {}
 foreach n {monitor_status monitor_boot_ticks monitor_rx_ticks monitor_tx_ticks observer_alignment observer_rt_words observer_rt_frames observer_aux_words observer_aux_frames} {
  lappend values [rd $n]
 }
 puts "EXTERNAL_SAMPLE $values"
}
if {[rd monitor_magic]!=0x44525430} {error "Wrong diagnostic PL"}
wr monitor_tx_enable 0
wr monitor_reset 1
wr observer_enable 0
wr monitor_loopback 0
wr monitor_prbs 0
wr monitor_tx_prbs 0
after 50
wr monitor_reset 0
after 2000
wr observer_enable 1
after 100
sample
for {set i 0} {$i<3} {incr i} {after 500; sample}
wr observer_enable 0
wr monitor_tx_enable 0
puts "EXTERNAL_OBSERVATION_COMPLETE"
disconnect

