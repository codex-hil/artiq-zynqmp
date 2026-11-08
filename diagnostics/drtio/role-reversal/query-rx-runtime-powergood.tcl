# Diagnostic runtime model corresponding to generated wizard XDC power-on-done.
set selected {}
foreach cell [get_cells -hierarchical -filter {NAME =~ *pwr_on_fsm*}] {
    if {[regexp {(^|[/.])pwr_on_fsm_reg$} [get_property NAME $cell]]} {lappend selected $cell}
}
if {[llength $selected] != 1} {error "Expected one power-on-done register, got$selected"}
set pin [get_pins -of_objects $selected -filter {REF_PIN_NAME == Q}]
if {[llength $pin] != 1} {error "Expected one power-on-done Q pin"}
set_case_analysis 1 $pin
update_timing
set out [open rx-runtime-powergood.tsv w]
puts $out "POWERGOOD_CASE\t$pin\t1"
foreach clock [get_clocks] {
    puts $out "CLOCK\t$clock\t[get_property PERIOD $clock]\t[get_property SOURCE_PINS $clock]"
}
close $out
report_clocks -file rx-runtime-powergood.rpt
puts "RX_RUNTIME_POWERGOOD_QUERY_COMPLETE"
