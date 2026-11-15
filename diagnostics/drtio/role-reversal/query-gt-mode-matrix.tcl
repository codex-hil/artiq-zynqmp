# SPDX-License-Identifier: LGPL-3.0-or-later
# Six diagnostic mode assumptions, overwrite ALL nine case pins every case.
# Never save DCP, override periods, import vendor exceptions or claim reachability.
set_param general.maxThreads 4
open_checkpoint /srv/nvme-fast-1/vivado-work/genesys-retained-local-cdc-20261112-v1/combined_cdc.dcp
report_clocks -file baseline-clocks.rpt
set gt [get_cells -hierarchical -filter {REF_NAME == GTHE4_CHANNEL}]
if {[llength $gt]!=1} {error "Expected one GT primitive"}
set selected {}
foreach pin [get_pins -of_objects $gt] {
 if {[regexp {^(TXOUTCLKSEL|RXOUTCLKSEL|RXRATE)\[([0-2])\]$} [get_property REF_PIN_NAME $pin] -> kind bit]} {lappend selected [list $pin $kind $bit]}
}
if {[llength $selected]!=9} {error "Expected exactly nine case pins"}
set out [open matrix.tsv w]
foreach tx {000 101 010} {
 foreach rxrate {001 000} {
  set label "tx${tx}_rxrate${rxrate}"
  puts $out "MODE\t$label"
  foreach item $selected {
   lassign $item pin kind bit
   if {$kind eq "TXOUTCLKSEL"} {set word $tx} elseif {$kind eq "RXRATE"} {set word $rxrate} else {set word "010"}
   set value [string index $word [expr {2-$bit}]]
   set_case_analysis $value $pin
   puts $out "CASE\t$label\t[get_property REF_PIN_NAME $pin]\t$value"
  }
  update_timing
  foreach clock [get_clocks] {puts $out "CLOCK\t$label\t$clock\t[get_property PERIOD $clock]\t[get_property SOURCE_PINS $clock]"}
  foreach buffer [get_cells -hierarchical -filter {REF_NAME == BUFG_GT}] {
   set pin [get_pins -of_objects $buffer -filter {REF_PIN_NAME == O}]
   puts $out "BUFFER\t$label\t$buffer\t[get_clocks -quiet -of_objects $pin]"
  }
  report_clocks -file "${label}-clocks.rpt"
 }
}
close $out
close_design
puts "GT_SIX_MODE_MATRIX_COMPLETE"
