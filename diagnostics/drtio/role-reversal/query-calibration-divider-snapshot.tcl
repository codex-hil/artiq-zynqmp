# SPDX-License-Identifier: LGPL-3.0-or-later
# Temporary in-memory divider attribute snapshot, NOT DRP sequencing proof.
set_param general.maxThreads 4
open_checkpoint /srv/nvme-fast-1/vivado-work/genesys-retained-local-cdc-20261112-v1/combined_cdc.dcp
set gt [get_cells -hierarchical -filter {REF_NAME == GTHE4_CHANNEL}]
if {[llength $gt]!=1} {error "Expected one GT"}
set original [get_property TX_PROGDIV_CFG $gt]
if {$original!=0} {error "Unexpected static TX divider $original"}
set out [open snapshot.tsv w]
puts $out "ORIGINAL_TX_PROGDIV_CFG\t$original"
foreach pin [get_pins -of_objects $gt] {
 if {[regexp {^(TXOUTCLKSEL|RXOUTCLKSEL|RXRATE)\[([0-2])\]$} [get_property REF_PIN_NAME $pin] -> kind bit]} {
  if {$kind eq "TXOUTCLKSEL"} {set word "101"} elseif {$kind eq "RXOUTCLKSEL"} {set word "010"} else {set word "000"}
  set value [string index $word [expr {2-$bit}]]
  set_case_analysis $value $pin
  puts $out "CASE\t[get_property REF_PIN_NAME $pin]\t$value"
 }
}
set_property TX_PROGDIV_CFG 20.0 $gt
puts $out "TEMPORARY_TX_PROGDIV_CFG\t[get_property TX_PROGDIV_CFG $gt]"
update_timing
foreach clock [get_clocks] {puts $out "CLOCK\t$clock\t[get_property PERIOD $clock]\t[get_property SOURCE_PINS $clock]"}
close $out
report_clocks -file snapshot-clocks.rpt
close_design
puts "CALIBRATION_DIVIDER_SNAPSHOT_COMPLETE_NO_SAVE"
