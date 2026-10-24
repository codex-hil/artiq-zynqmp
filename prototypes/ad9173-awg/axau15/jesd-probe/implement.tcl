set_param general.maxThreads 4
open_checkpoint synth.dcp
# Scope CDC exceptions to first-stage synchronizer D pins; never whole clocks.
set first {}
foreach n [get_nets -hier -filter {MR_FF == TRUE}] {
 foreach p [get_pins -of_objects $n -filter {DIRECTION == OUT}] {
  set c [get_cells -of_objects $p]
  if {[get_property ASYNC_REG $c] ne "1" && [get_property ASYNC_REG $c] ne "TRUE"} {error "MR_FF driver lacks ASYNC_REG: $c"}
  lappend first {*}[get_pins -of_objects $c -filter {REF_PIN_NAME == D}]
 }
}
set first [lsort -unique $first]
if {[llength $first]<8} {error "Missing Migen synchronizers"}
proc bound_async {dest budget} {
 foreach d $dest {
  set d [get_pins $d]
  set src [all_fanin -flat -startpoints_only -to $d]
  if {[llength $src]} {set_max_delay -datapath_only $budget -from $src -to $d}
 }
}
bound_async $first 6.5
set f [open cdc-endpoints.txt w];foreach p $first {puts $f $p};close $f
# Async assertion / synchronized release in generated reset synchronizers.
set resets [get_cells -hier -filter {REF_NAME == FDPE && ASYNC_REG == TRUE}]
if {[llength $resets]!=34} {error "Reset synchronizer count changed"}
set_false_path -to [get_pins -of_objects $resets -filter {REF_PIN_NAME == PRE}]
foreach {port target} {miso spi_gpio/core/miso_sync_reg[0]/D spi_en spi_gpio/core/owner_sync_reg[0]/D} {
 set p [get_pins $target];if {[llength $p]!=1} {error "Missing input synchronizer"}
 set_max_delay -datapath_only 20 -from [get_ports $port] -to $p
}
set status [get_cells -hier -regexp {^status_scan/meta_reg\[[0-9]+\]}]
if {[llength $status]!=9} {error "Status synchronizer count"}
bound_async [get_pins -of_objects $status -filter {REF_PIN_NAME == D}] 20
# Optional USER3 acknowledged bundled-data mailbox. Held sample cannot change
# until returned acknowledgement. Destination samples after two request stages.
set held [get_cells -quiet -hier -regexp {^payload_scan/core/held_reg\[[0-9]+\]}]
if {[llength $held]} {
 if {[llength $held]!=16} {error "Payload held width"}
 set amp [get_cells -hier -regexp {^payload_scan/core/amplitude_reg\[[0-9]+\]}]
 if {[llength $amp]!=16} {error "Payload destination width"}
 set_max_delay -datapath_only 6.0 -from $held -to $amp
 set_bus_skew 6.0 -from $held -to $amp
 foreach name {req_sync ack_sync} {
  set d [get_pins [format {payload_scan/core/%s_reg[0]/D} $name]]
  if {[llength $d]!=1} {error "Payload handshake synchronizer missing"}
  bound_async $d 6.0
 }
}
set outputs [get_ports {sck mosi cs_dac cs_clock}]
set pinregs [get_cells -hier -filter {NAME =~ spi_gpio/core/pins_reg*}]
if {[llength $pinregs]!=4} {error "GPIO register count"}
set_max_delay -datapath_only 30 -from $pinregs -to $outputs
set_max_delay -datapath_only 30 -from [get_ports spi_en] -to $outputs
set_property DRIVE 4 $outputs
opt_design
place_design
route_design
report_timing_summary -report_unconstrained -file timing.rpt
report_cdc -details -file cdc.rpt
report_drc -file drc.rpt
report_utilization -file utilization.rpt
report_io -file io.rpt
set f [open gt-locations.txt w]
foreach c [get_cells -hier -filter {REF_NAME =~ GTHE4_* || REF_NAME == IBUFDS_GTE4}] {puts $f "$c [get_property REF_NAME $c] [get_property LOC $c]"}
close $f
write_checkpoint -force routed.dcp
if {[llength [get_timing_paths -delay_type max -slack_lesser_than 0]] || [llength [get_timing_paths -delay_type min -slack_lesser_than 0]]} {error "Timing failure"}
write_bitstream -force jesd_probe.bit
