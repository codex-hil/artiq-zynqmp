open_hw_manager
connect_hw_server -url localhost:3121
set ts [get_hw_targets -filter {NAME =~ *210512180081}]
if {[llength $ts]!=1} {error "Cable mismatch"}
current_hw_target [lindex $ts 0]
set_property PARAM.FREQUENCY 6000000 [current_hw_target]
open_hw_target
set ds [get_hw_devices]
if {[llength $ds]!=1} {error "Unexpected JTAG chain"}
set d [lindex $ds 0]
if {[get_property PART $d] ne "xcau15p" || [string toupper [get_property IDCODE_HEX $d]] ne "04AC2093"} {error "FPGA identity mismatch"}
set_property PROGRAM.FILE {/srv/codex-hil-data/artiq-zynqmp/artifacts/alinx-payload-20261024a/jesd_probe.bit} $d
program_hw_devices $d
refresh_hw_device $d
report_property $d
close_hw_target
disconnect_hw_server
close_hw_manager
