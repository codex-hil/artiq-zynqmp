# Diagnostic exact runtime RXRATE000 pin cases, no frequency override.
set gt [get_cells -hierarchical -filter {REF_NAME == GTHE4_CHANNEL}]
if {[llength $gt] != 1} {error "Expected one GT primitive"}
set selected {}
foreach pin [get_pins -of_objects $gt] {
    if {[regexp {^RXRATE\[([0-2])\]$} [get_property REF_PIN_NAME $pin]]} {
        set_case_analysis 0 $pin
        lappend selected $pin
    }
}
if {[llength $selected] != 3} {error "Expected three RXRATE pins, got$selected"}
update_timing
set out [open rxrate-runtime.tsv w]
foreach pin $selected {
    set value unknown
    foreach property {CASE_VALUE CASE_ANALYSIS} {
        if {[lsearch -exact [list_property $pin] $property] >= 0} {set value [get_property $property $pin]}
    }
    puts $out "RXRATE_CASE\t$pin\t$value"
}
foreach clock [get_clocks] {
    puts $out "CLOCK\t$clock\t[get_property PERIOD $clock]\t[get_property SOURCE_PINS $clock]"
}
close $out
report_clocks -file rxrate-runtime.rpt
puts "RXRATE_RUNTIME_QUERY_COMPLETE"
