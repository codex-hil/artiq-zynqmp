set_param general.maxThreads 4
create_project -in_memory -part xcau15p-ffvb676-2-i
read_verilog {core.v top.v}
synth_design -top spi_probe -part xcau15p-ffvb676-2-i
foreach {port pin} {sck N21 mosi N22 miso R25 cs_dac R26 cs_clock P25 spi_en P26} {set_property PACKAGE_PIN $pin [get_ports $port]}
set_property IOSTANDARD LVCMOS18 [get_ports {miso spi_en sck mosi cs_dac cs_clock}]
set_property PACKAGE_PIN V7 [get_ports ref_p]
set_property PACKAGE_PIN V6 [get_ports ref_n]
create_clock -name fmc245 -period 4.069010417 [get_ports ref_p]
set_property SLEW SLOW [get_ports {sck mosi cs_dac cs_clock}]
set_property DRIVE 4 [get_ports {sck mosi cs_dac cs_clock}]
set_property BITSTREAM.CONFIG.UNUSEDPIN PULLNONE [current_design]
create_clock -name jtag10 -period 100 [get_pins bs/INTERNAL_TCK]
# External inputs are asynchronous, each has a two-flop TCK synchronizer.
# Physical budgets, not a fictitious free-running SPI clock. Host holds each
# pin state for an entire 64-bit scan (>6.4us at the supported <=10MHz TCK).
foreach {port target} {miso core/miso_sync_reg[0]/D spi_en core/owner_sync_reg[0]/D} {
 set p [get_pins $target]
 if {[llength $p]!=1} {error "Missing input synchronizer $target"}
 set_max_delay -datapath_only 20 -from [get_ports $port] -to $p
}
set outputs [get_ports {sck mosi cs_dac cs_clock}]
set pinregs [get_cells -hier -filter {NAME =~ core/pins_reg*}]
if {[llength $pinregs]!=4} {error "GPIO output register mismatch"}
set_max_delay -datapath_only 30 -from $pinregs -to $outputs
set_max_delay -datapath_only 30 -from [get_ports spi_en] -to $outputs
create_clock -name probe_jtag10 -period 100 [get_pins probe_bs/INTERNAL_TCK]
set from_gray [get_cells -hier -regexp {^gray_reg\[[0-9]+\]}]
set to_meta [get_cells -hier -regexp {^meta_reg\[[0-9]+\]}]
if {[llength $from_gray]!=32 || [llength $to_meta]!=32} {error "Gray CDC endpoint mismatch"}
set_max_delay -datapath_only 8.138 -from $from_gray -to $to_meta
set_bus_skew 8.138 -from $from_gray -to $to_meta
opt_design
place_design
route_design
report_timing_summary -report_unconstrained -file timing.rpt
report_cdc -file cdc.rpt
report_bus_skew -file skew.rpt
report_drc -file drc.rpt
report_utilization -file utilization.rpt
if {[llength [get_timing_paths -delay_type max -slack_lesser_than 0]] || [llength [get_timing_paths -delay_type min -slack_lesser_than 0]]} {error "Timing failure"}
write_checkpoint -force routed.dcp
write_bitstream -force refclk_probe.bit
