# SPDX-License-Identifier: LGPL-3.0-or-later
# Read-only full combined checkpoint endpoint capture; no design mutation.
set_param general.maxThreads 4
open_checkpoint /srv/nvme-fast-1/vivado-work/genesys-combined-synth-cdc-20261110-v1/combined_cdc.dcp
set targets {
 {FDPE/PRE}
 {FDPE_10/PRE}
 {FDPE_12/PRE}
 {FDPE_14/PRE}
 {FDPE_16/PRE}
 {FDPE_18/PRE}
 {FDPE_20/PRE}
 {FDPE_22/PRE}
 {FDPE_24/PRE}
 {FDPE_28/PRE}
 {FDPE_6/PRE}
 {FDPE_8/PRE}
 {drtio_gth/inst/gen_gtwizard_gthe4_top.drtio_gth_gtwizard_gthe4_inst/gen_gtwizard_gthe4.gen_cpll_cal_gthe4.gen_cpll_cal_inst[0].gen_inst_cpll_cal.gtwizard_ultrascale_v1_7_22_gthe4_cpll_cal_inst/gtwizard_ultrascale_v1_7_22_gthe4_cpll_cal_tx_i/U_TXOUTCLK_FREQ_COUNTER/reset_synchronizer_testclk_rst_inst/rst_in_meta_reg/PRE}
 {drtio_gth/inst/gen_gtwizard_gthe4_top.drtio_gth_gtwizard_gthe4_inst/gen_gtwizard_gthe4.gen_cpll_cal_gthe4.gen_cpll_cal_inst[0].gen_inst_cpll_cal.gtwizard_ultrascale_v1_7_22_gthe4_cpll_cal_inst/gtwizard_ultrascale_v1_7_22_gthe4_cpll_cal_tx_i/U_TXOUTCLK_FREQ_COUNTER/tstclk_rst_dly1_reg/D}
 {xilinxmultiregimpl420_reg/D}
 {xilinxmultiregimpl430_reg/D}
}
set out [open fanins.tsv w]
set cones {}
foreach name $targets {
 set pin [get_pins -quiet -hierarchical -filter "NAME == \"$name\""]
 if {[llength $pin]!=1} {error "Endpoint not unique: $name"}
 set starts [all_fanin -flat -startpoints_only -to $pin]
 set cells [all_fanin -flat -only_cells -to $pin]
 puts $out "ENDPOINT\t$name\t[join [lsort $starts] ,]\t[join [lsort $cells] ,]"
 foreach cell $cells {dict set cones $cell 1}
}
close $out
set out [open network.tsv w]
foreach cell [lsort [dict keys $cones]] {
 set ref [get_property REF_NAME [get_cells $cell]]
 set init ""
 if {[string match LUT* $ref] || [string match FD* $ref]} {set init [get_property INIT [get_cells $cell]]}
 puts $out "CELL\t$cell\t$ref\t$init"
 foreach pin [get_pins -of_objects [get_cells $cell]] {
  puts $out "PIN\t$pin\t[get_property DIRECTION $pin]\t[join [get_nets -of_objects $pin] ,]"
 }
}
close $out
close_design
puts "COMBINED_FANINS_READONLY_COMPLETE"
