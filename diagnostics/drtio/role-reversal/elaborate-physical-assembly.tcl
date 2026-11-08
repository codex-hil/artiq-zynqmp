# RTL/IP binding elaboration only. No logic synthesis or board implementation.
set_param general.maxThreads 4
create_project -force master_elab ./project -part xczu5ev-sfvc784-1-e
read_verilog [glob drtio_gth/hdl/*.v]
read_verilog [glob drtio_gth/synth/*.v]
read_verilog master_physical_candidate.v
synth_design -rtl -top master_physical_candidate -part xczu5ev-sfvc784-1-e
set out [open unresolved.txt w]
foreach cell [get_cells -hierarchical -filter {IS_BLACKBOX == 1}] {puts $out $cell}
close $out
puts "MASTER_PHYSICAL_RTL_IP_ELABORATION_COMPLETE"
