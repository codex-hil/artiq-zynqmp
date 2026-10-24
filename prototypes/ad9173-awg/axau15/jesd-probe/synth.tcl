set_param general.maxThreads 4
create_project -in_memory -part xcau15p-ffvb676-2-i
read_verilog {axau15_jesd.v core.v spi_gpio.v status_scan.v}
synth_design -top axau15_jesd -part xcau15p-ffvb676-2-i
source constraints.tcl
set_property LOC GTHE4_COMMON_X0Y1 [get_cells -hier -filter {REF_NAME == GTHE4_COMMON}]
foreach c [get_cells -hier -filter {REF_NAME == BSCANE2}] {create_clock -name [string map {/ _} $c] -period 100 [get_pins $c/INTERNAL_TCK]}
report_cdc -details -file cdc-synth.rpt
report_timing_summary -report_unconstrained -file timing-synth.rpt
set f [open async-cells.txt w]
foreach c [get_cells -hier -filter {ASYNC_REG == TRUE}] {puts $f $c}
close $f
write_checkpoint -force synth.dcp
