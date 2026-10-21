# Offline only: never opens a hardware manager.
set_param general.maxThreads 8
set parts [get_parts -quiet *xcau15p*]
puts "AXAU15_PARTS=$parts"
set exact [get_parts -quiet xcau15p-ffvb676-2-i]
if {[llength $exact] != 1} {error "Exact XCAU15P-2FFVB676I not installed"}
report_property $exact
create_project -in_memory -part $exact
set f [open probe.v w]
puts $f {module probe(input clk, input d, output reg q); always @(posedge clk) q <= d; endmodule}
close $f
read_verilog probe.v
synth_design -top probe -part $exact
write_checkpoint -force probe.dcp
puts "AXAU15_EXACT_PART_SYNTHESIS_PASS"
