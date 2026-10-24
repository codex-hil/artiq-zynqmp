set_param general.maxThreads 4
create_project -in_memory -part xcau15p-ffvb676-2-i
read_verilog {axau15_jesd.v core.v spi_gpio.v status_scan.v eth_scan.v}
foreach f [split [string trim [read [set fp [open ipbus-order.txt r]]]] "\n"] {read_vhdl -vhdl2008 ipbus/$f}
close $fp
synth_design -top axau15_jesd -part xcau15p-ffvb676-2-i
source constraints.tcl
set_property LOC GTHE4_COMMON_X0Y1 [get_cells -hier -filter {REF_NAME == GTHE4_COMMON}]
foreach c [get_cells -hier -filter {REF_NAME == BSCANE2}] {create_clock -name [string map {/ _} $c] -period 100 [get_pins $c/INTERNAL_TCK]}
foreach {port pin} {eth_rx_clk AD21 eth_rx_ctl AE21 eth_rx_data[0] AC22 eth_rx_data[1] AC23 eth_rx_data[2] AD23 eth_rx_data[3] AE23 eth_tx_clk AE16 eth_tx_ctl AD16 eth_tx_data[0] Y18 eth_tx_data[1] AA18 eth_tx_data[2] AB24 eth_tx_data[3] AC24 eth_rst_n AF23 eth_mdc AF20 eth_mdio AE18} {
 set_property PACKAGE_PIN $pin [get_ports $port]
 set_property IOSTANDARD LVCMOS18 [get_ports $port]
}
create_clock -name rgmii_rx -period 8 [get_ports eth_rx_clk]
# PHY clock centered in a4ns DDR eye. The NEXT transition is1.4..2.6ns
# after each clock edge (equivalently previous transition -2.6..-1.4ns).
set rx [get_ports {eth_rx_ctl eth_rx_data[*]}]
foreach fall {0 1} {
 if {$fall} {
  set_input_delay -clock rgmii_rx -clock_fall -add_delay -min 1.4 $rx
  set_input_delay -clock rgmii_rx -clock_fall -add_delay -max 2.6 $rx
 } else {
  set_input_delay -clock rgmii_rx -min 1.4 $rx
  set_input_delay -clock rgmii_rx -max 2.6 $rx
 }
}
report_cdc -details -file cdc-synth.rpt
report_timing_summary -report_unconstrained -file timing-synth.rpt
set f [open names.txt w]
foreach c [get_cells -hier -filter {NAME =~ *config* || NAME =~ *active* || REF_NAME == ODDRE1 || ASYNC_REG == TRUE}] {puts $f "$c [get_property REF_NAME $c]"}
close $f
write_checkpoint -force synth.dcp
