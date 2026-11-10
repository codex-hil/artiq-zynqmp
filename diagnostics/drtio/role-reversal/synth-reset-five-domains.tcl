# Isolated reset-only logic synthesis and diagnostic CDC. No timing exceptions.
set_param general.maxThreads 4
create_project -force reset_cdc ./project -part xczu5ev-sfvc784-1-e
read_verilog reset_five_domains.v
synth_design -top reset_five_domains -part xczu5ev-sfvc784-1-e -mode out_of_context
foreach {port period} {management_clock 8 control_clock 10 ps_clock 8 tx_clock 14 rx_clock 18} {
 set found [get_ports $port]
 if {[llength $found] != 1} {error "Clock port not unique: $port"}
 create_clock -name $port -period $period $found
}
report_clocks -file clocks.rpt
report_cdc -details -file cdc.rpt
report_exceptions -file exceptions.rpt
report_timing_summary -file timing.rpt
report_utilization -file utilization.rpt
set out [open registers.tsv w]
foreach cell [lsort [get_cells -hierarchical -filter {REF_NAME =~ FD*}]] {
 puts $out "$cell\t[get_property REF_NAME $cell]\t[get_property INIT $cell]\t[get_property ASYNC_REG $cell]"
}
close $out
write_checkpoint -force reset_cdc.dcp
puts "RESET_FIVE_DOMAIN_LOGIC_SYNTH_CDC_COMPLETE"
