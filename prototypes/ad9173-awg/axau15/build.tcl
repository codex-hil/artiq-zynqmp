# Run from a NEW packaged input directory on Dell, under the global build lock.
# Synthesis and pin audit only; implementation/bitstream are not yet qualified.
set_param general.maxThreads 8
set part [get_parts -quiet xcau15p-ffvb676-2-i]
if {[llength $part] != 1} {error "Install exact Artix UltraScale+ device support first"}
create_project -in_memory -part $part
read_verilog axau15_awg.v
read_verilog spi-console.v
synth_design -top axau15_awg -part $part
source constraints.tcl
report_io -file io.rpt
report_utilization -file utilization.rpt
report_clocks -file clocks.rpt
report_cdc -file cdc.rpt
report_drc -file drc.rpt
set f [open package-pins.txt w]
foreach pin {T24 U24 V7 V6 AA5 AA4 W5 W4 U5 U4 R5 R4 V24 W24 N24 P24 N21 N22 R25 R26 P25 P26} {
    set p [get_package_pins -quiet $pin]
    if {[llength $p] != 1} {error "Missing package pin $pin"}
    puts $f "$pin [get_property PIN_FUNC $p]"
}
close $f
write_checkpoint -force axau15-synth.dcp
puts "AXAU15_SYNTHESIS_COMPLETE_NOT_IMPLEMENTED"
