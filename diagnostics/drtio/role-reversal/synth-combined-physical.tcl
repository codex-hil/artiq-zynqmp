# SPDX-License-Identifier: LGPL-3.0-or-later
# Diagnostic OOC logic synthesis only. No board constraints or timing waivers.
set_param general.maxThreads 4
create_project -force combined_cdc ./project -part xczu5ev-sfvc784-1-e
read_verilog [glob drtio_gth/hdl/*.v]
read_verilog [glob drtio_gth/synth/*.v]
read_verilog master_physical_candidate.v
synth_design -top master_physical_candidate -part xczu5ev-sfvc784-1-e -mode out_of_context
foreach {port period} {pl_clk0 8 ref_p 6.4} {
 set found [get_ports $port]
 if {[llength $found] != 1} {error "Clock port not unique: $port"}
 create_clock -name diagnostic_$port -period $period $found
}
report_clocks -file clocks.rpt
report_cdc -details -file cdc.rpt
report_exceptions -file exceptions.rpt
check_timing -verbose -file check-timing.rpt
report_utilization -file utilization.rpt
set out [open unresolved.txt w]
foreach cell [get_cells -quiet -hierarchical -filter {IS_BLACKBOX == 1}] {puts $out $cell}
close $out
set out [open registers.tsv w]
foreach cell [lsort [get_cells -hierarchical -filter {REF_NAME =~ FD*}]] {
 puts $out "$cell\t[get_property REF_NAME $cell]\t[get_property INIT $cell]\t[get_property ASYNC_REG $cell]"
}
close $out
write_checkpoint -force combined_cdc.dcp
puts "COMBINED_LOGIC_SYNTH_CDC_COMPLETE"
