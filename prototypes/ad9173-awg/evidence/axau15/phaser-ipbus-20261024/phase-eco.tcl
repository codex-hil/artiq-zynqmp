set_param general.maxThreads 4
open_checkpoint routed-input.dcp
set_property CLKOUT0_PHASE -90 [get_cells rx_cm_mmcm]
report_property [get_cells rx_cm_mmcm] -file rx-mmcm.rpt
report_timing_summary -report_unconstrained -file timing.rpt
report_cdc -details -file cdc.rpt
report_drc -file drc.rpt
report_bus_skew -file bus-skew.rpt
report_utilization -file utilization.rpt
report_io -file io.rpt
write_checkpoint -force routed.dcp
if {[llength [get_timing_paths -delay_type max -slack_lesser_than 0]] || [llength [get_timing_paths -delay_type min -slack_lesser_than 0]]} {error "Timing failure"}
write_bitstream -force phaser_ipbus.bit
