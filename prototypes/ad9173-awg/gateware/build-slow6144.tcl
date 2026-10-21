# Trenz reference only; do not program this pinout on AXAU15.
set root [file dirname [file normalize [info script]]]
cd $root
set_param general.maxThreads 8
create_project -in_memory -part xczu4ev-sfvc784-1-e
read_verilog $root/fabric_jesd_tx.v
read_verilog $root/spi-console.v
synth_design -top fabric_jesd_tx
foreach {port pin} {ref_p AF7 ref_n AF6 tx0_p W4 tx0_n W3 tx1_p U4 tx1_n U3 tx2_p R4 tx2_n R3 tx3_p N4 tx3_n N3 sync0_p AE5 sync0_n AF5 sync1_p AB8 sync1_n AC8 led B15 sck AC9 mosi AD9 miso AE9 cs_dac AE8 cs_clock AG9 spi_en AH9} {set_property PACKAGE_PIN $pin [get_ports $port]}
set_property IOSTANDARD LVDS [get_ports {ref_p ref_n sync0_p sync0_n sync1_p sync1_n}]
set_property IOSTANDARD LVCMOS18 [get_ports {led sck mosi miso cs_dac cs_clock spi_en}]
set_property SLEW SLOW [get_ports {sck mosi cs_dac cs_clock}]
create_clock -name fabric_reference -period 4.069010417 [get_ports ref_p]
create_clock -name config_osc -period 10 [get_pins -hier -filter {REF_PIN_NAME == CFGMCLK}]
set_clock_groups -asynchronous -group [get_clocks config_osc] -group [get_clocks fabric_reference]
set_false_path -to [get_cells -hier -filter {NAME =~ *scan_reg*}]
set_property BITSTREAM.CONFIG.UNUSEDPIN PULLNONE [current_design]
set qpll_refout_port QPLL1OUTREFCLK
set qpll_refout_period 4.069010417
source $root/fabric-clock-constraints.tcl
create_clock -name spi_jtag_tck -period 100 [get_pins -hier -filter {NAME =~ *bs/TCK}]
set_clock_groups -asynchronous -group [get_clocks spi_jtag_tck] -group [get_clocks -include_generated_clocks {config_osc fabric_reference qpll_refout_model jtag_drck}]
set_false_path -from [get_ports {miso spi_en}]
set_false_path -to [get_ports {sck mosi cs_dac cs_clock}]
opt_design
place_design
route_design
report_drc -file $root/fabric-drc.rpt
report_timing_summary -file $root/fabric-timing.rpt
report_utilization -file $root/fabric-utilization.rpt
write_checkpoint -force $root/fabric_spi_slow6144.dcp
write_bitstream -force $root/fabric_spi_slow6144.bit
