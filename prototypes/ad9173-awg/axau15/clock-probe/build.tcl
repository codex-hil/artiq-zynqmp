set_param general.maxThreads 4
create_project -in_memory -part xcau15p-ffvb676-2-i
read_verilog top.v
synth_design -top clock_probe -part xcau15p-ffvb676-2-i
set_property PACKAGE_PIN T24 [get_ports sys_p]
set_property PACKAGE_PIN U24 [get_ports sys_n]
set_property IOSTANDARD LVDS [get_ports {sys_p sys_n}]
set_property BITSTREAM.CONFIG.UNUSEDPIN PULLNONE [current_design]
create_clock -name sys200 -period 5 [get_ports sys_p]
create_clock -name jtag10 -period 100 [get_pins bs/INTERNAL_TCK]
set from_gray [get_cells -hier -regexp {^gray_reg\[[0-9]+\]}]
set to_meta [get_cells -hier -regexp {^meta_reg\[[0-9]+\]}]
if {[llength $from_gray]!=32 || [llength $to_meta]!=32} {error "Gray CDC endpoint mismatch"}
set_max_delay -datapath_only 10 -from $from_gray -to $to_meta
set_bus_skew 10 -from $from_gray -to $to_meta
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
write_bitstream -force clock_probe.bit
