set_param general.maxThreads 4
open_checkpoint synth.dcp
# Match rgmii.py; explicit also when reusing an earlier synthesized checkpoint.
set_property CLKOUT0_PHASE -90 [get_cells rx_cm_mmcm]
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
# LiteX RX MMCM reset delay is an eight-FF chain clocked by raw RGMII RX.
# Preserve/mark the chain and constrain only its asynchronous first D pin.
set chain {};set next [get_pins rx_cm_mmcm/RST]
for {set i 0} {$i<8} {incr i} {
 set q [get_pins -of_objects [get_nets -of_objects $next] -filter {DIRECTION == OUT}]
 set c [get_cells -of_objects $q]
 if {[llength $c]!=1 || [get_property REF_NAME $c] ne "FDCE"} {error "RX MMCM reset chain changed"}
 lappend chain $c
 set next [get_pins -of_objects $c -filter {REF_PIN_NAME == D}]
}
set_property ASYNC_REG TRUE $chain
set_property DONT_TOUCH TRUE $chain
bound_async $next 6.5

# Async assertion / synchronized release in generated reset synchronizers.
set resets [get_cells -hier -filter {REF_NAME == FDPE && ASYNC_REG == TRUE}]
if {[llength $resets]<34} {error "Reset synchronizer count changed"}
set_false_path -to [get_pins -of_objects $resets -filter {REF_PIN_NAME == PRE}]
foreach {port target} {miso spi_gpio/core/miso_sync_reg[0]/D spi_en spi_gpio/core/owner_sync_reg[0]/D} {
 set p [get_pins $target];if {[llength $p]!=1} {error "Missing input synchronizer"}
 set_max_delay -datapath_only 20 -from [get_ports $port] -to $p
}
set status [get_cells -hier -regexp {^status_scan/meta_reg\[[0-9]+\]}]
if {[llength $status]!=9} {error "Status synchronizer count"}
bound_async [get_pins -of_objects $status -filter {REF_PIN_NAME == D}] 20
set outputs [get_ports {sck mosi cs_dac cs_clock}]
set pinregs [get_cells -hier -filter {NAME =~ spi_gpio/core/pins_reg*}]
if {[llength $pinregs]!=4} {error "GPIO register count"}
set_max_delay -datapath_only 30 -from $pinregs -to $outputs
set_max_delay -datapath_only 30 -from [get_ports spi_en] -to $outputs
set_property DRIVE 4 $outputs
# Ethernet JTAG diagnostic: independent status bits and host-paced MDIO.
set ethmeta [get_cells -hier -regexp {^eth_scan/meta_reg\[[0-9]+\]}]
if {[llength $ethmeta]!=5} {error "Ethernet status synchronizer count"}
bound_async [get_pins -of_objects $ethmeta -filter {REF_PIN_NAME == D}] 20
set md [get_ports eth_mdio]
set mds [all_fanout -flat -endpoints_only -from $md]
set_max_delay -datapath_only 20 -from $md -to $mds
foreach port {eth_mdc eth_mdio eth_rst_n} {
 set dst [get_ports $port]
 set src [all_fanin -flat -startpoints_only -to $dst]
 if {[llength $src]} {set_max_delay -datapath_only 30 -from $src -to $dst}
}
# Explicit, held-data request/ack bank. Preserve these FFs outside DSP AREGs.
set held [get_cells -hier -filter {NAME =~ *registers_config_held_reg*}]
set active [get_cells -hier -filter {NAME =~ *generator_config_active_reg*}]
set clr [get_cells -hier -filter {NAME =~ *generator_clear_reg*}]
if {[llength $held]<643 || [llength $active]<642} {error "Incomplete DDS config banks"}
set_max_delay -datapath_only 6.0 -from $held -to [concat $active $clr]
set_bus_skew 6.0 -from $held -to [concat $active $clr]
# Gray FIFO pointers: retain a skew constraint in addition to first-stage max delay.
set groups [dict create]
foreach src [get_cells -hier -regexp {.*graycounter[0-9]+_q_reg\[[0-9]+\]}] {
 regsub {\[[0-9]+\]$} $src {} key
 dict lappend groups $key $src
}
set fifo_groups 0
foreach key [dict keys $groups] {
 set src [dict get $groups $key];set dst {}
 foreach endpoint [all_fanout -flat -endpoints_only -from [get_pins -of_objects $src -filter {REF_PIN_NAME == Q}]] {
  if {$endpoint in $first} {lappend dst $endpoint}
 }
 if {[llength $dst]} {set_bus_skew 6.0 -from $src -to $dst;incr fifo_groups}
}
if {$fifo_groups<2} {error "Missing RX FIFO Gray groups"}
# Model PHY TX capture after its2ns internal clock delay; setup/hold1ns plus0.2ns PCB budget.
set mm [get_cells -hier -filter {REF_NAME == MMCME4_ADV && NAME =~ *net_cm*}]
if {[llength $mm]!=1} {error "Ethernet MMCM count"}
create_generated_clock -name rgmii_phy_capture -source [get_pins $mm/CLKOUT0] -edges {1 2 3} -edge_shift {2 2 2} [get_ports eth_tx_clk]
set tx [get_ports {eth_tx_ctl eth_tx_data[*]}]
set_output_delay -clock rgmii_phy_capture -max 1.2 $tx
set_output_delay -clock rgmii_phy_capture -min -1.2 $tx
set_output_delay -clock rgmii_phy_capture -clock_fall -add_delay -max 1.2 $tx
set_output_delay -clock rgmii_phy_capture -clock_fall -add_delay -min -1.2 $tx
set_property SLEW FAST [get_ports {eth_tx_clk eth_tx_ctl eth_tx_data[*]}]
set_property DRIVE 8 [get_ports {eth_tx_clk eth_tx_ctl eth_tx_data[*]}]

opt_design
place_design
route_design
report_timing_summary -report_unconstrained -file timing.rpt
report_cdc -details -file cdc.rpt
report_drc -file drc.rpt
report_bus_skew -file bus-skew.rpt
report_utilization -file utilization.rpt
report_io -file io.rpt
set f [open gt-locations.txt w]
foreach c [get_cells -hier -filter {REF_NAME =~ GTHE4_* || REF_NAME == IBUFDS_GTE4}] {puts $f "$c [get_property REF_NAME $c] [get_property LOC $c]"}
close $f
write_checkpoint -force routed.dcp
if {[llength [get_timing_paths -delay_type max -slack_lesser_than 0]] || [llength [get_timing_paths -delay_type min -slack_lesser_than 0]]} {error "Timing failure"}
write_bitstream -force phaser_ipbus.bit
