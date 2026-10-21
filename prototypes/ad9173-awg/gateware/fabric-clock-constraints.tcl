# GTGREFCLK test route lacks a timing arc to QPLL0OUTREFCLK in the AMD model.
# Explicit reference-output model; QPLL0OUTCLK/TXOUTCLK remain automatically derived.
if {![info exists qpll_refout_port]} {set qpll_refout_port QPLL0OUTREFCLK}
if {![info exists qpll_refout_period]} {set qpll_refout_period 5.425347222}
create_clock -name qpll_refout_model -period $qpll_refout_period [get_pins GTHE4_COMMON/$qpll_refout_port]
create_clock -name jtag_drck -period 100 [get_pins BSCANE2/DRCK]
set_clock_groups -name diagnostic_domains -asynchronous \
 -group [get_clocks -include_generated_clocks config_osc] \
 -group [get_clocks -include_generated_clocks {fabric_reference qpll_refout_model}] \
 -group [get_clocks -include_generated_clocks jtag_drck]
# Asynchronous SYNC pins enter explicit MultiReg synchronizers in the JESD cores.
set_false_path -from [get_ports {sync0_p sync0_n sync1_p sync1_n}]
# LED has no external sampling clock. BSCAN TDO is sampled by the JTAG hard block.
set_false_path -to [get_ports led]
set_max_delay 50 -datapath_only -from [get_clocks jtag_drck] -to [get_pins BSCANE2/TDO]
