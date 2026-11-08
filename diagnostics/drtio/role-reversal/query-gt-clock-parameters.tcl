# Bounded read-only elaborated primitive/clock-selector audit, no exceptions.
set cells [get_cells -hierarchical -filter {REF_NAME == GTHE4_CHANNEL}]
if {[llength $cells] != 1} {error "Expected one GTHE4_CHANNEL, got[llength $cells]"}
set gt [lindex $cells 0]
set out [open gt-parameters.tsv w]
foreach property [lsort [list_property $gt]] {
    if {[regexp {CPLL_(FBDIV|REFCLK_DIV)|[TR]X_(DATA_WIDTH|INT_DATAWIDTH|OUT_DIV|PROGDIV_CFG)} $property]} {
        puts $out "PARAM\t$property\t[get_property $property $gt]"
    }
}
foreach prefix {TXOUTCLKSEL RXOUTCLKSEL} {
    foreach pin [get_pins -of_objects $gt -filter "REF_PIN_NAME =~ ${prefix}*"] {
        set nets [get_nets -quiet -of_objects $pin]
        set drivers [get_pins -quiet -of_objects $nets -filter {DIRECTION == OUT}]
        puts $out "SELECT\t$pin\t$nets\t$drivers"
    }
}
foreach buffer [get_cells -hierarchical -filter {REF_NAME == BUFG_GT}] {
    foreach pin [get_pins -of_objects $buffer -filter {REF_PIN_NAME =~ DIV*}] {
        set nets [get_nets -quiet -of_objects $pin]
        set drivers [get_pins -quiet -of_objects $nets -filter {DIRECTION == OUT}]
        puts $out "DIVIDER\t$pin\t$nets\t$drivers"
    }
}
close $out
puts "GT_CLOCK_PARAMETER_QUERY_COMPLETE"
