# Exact divider receipt; no timing changes.
set cells [get_cells -hierarchical -filter {REF_NAME == GTHE4_CHANNEL}]
if {[llength $cells] != 1} {error "Expected one GT primitive"}
set gt [lindex $cells 0]
set out [open rx-divider.tsv w]
foreach property {RXOUT_DIV TXOUT_DIV CPLL_FBDIV CPLL_FBDIV_45 CPLL_REFCLK_DIV RX_DATA_WIDTH TX_DATA_WIDTH RX_INT_DATAWIDTH TX_INT_DATAWIDTH} {
    if {[lsearch -exact [list_property $gt] $property] < 0} {error "Missing $property"}
    set value [get_property $property $gt]
    if {$value eq ""} {error "Empty $property"}
    puts $out "PARAM\t$property\t$value"
}
foreach pin [get_pins -of_objects $gt] {
    set name [get_property REF_PIN_NAME $pin]
    if {[regexp {^(RXRATE|RXSYSCLKSEL|RXOUTCLKSEL)\[} $name]} {
        set nets [get_nets -segments -of_objects $pin]
        set drivers [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}]
        puts $out "PIN\t$name\t$drivers"
    }
}
close $out
puts "RX_DIVIDER_QUERY_COMPLETE"
