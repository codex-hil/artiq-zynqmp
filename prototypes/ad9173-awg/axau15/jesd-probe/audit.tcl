open_checkpoint routed.dcp
set gs [get_cells -hier -filter {REF_NAME == GTHE4_CHANNEL}]
set qs [get_cells -hier -filter {REF_NAME == GTHE4_COMMON}]
if {[llength $gs]!=4 || [llength $qs]!=1} {error "GT count mismatch"}
if {[get_property LOC $qs] ne "GTHE4_COMMON_X0Y1"} {error "QPLL bank mismatch"}
set nets {}
foreach g $gs {
 foreach p {TXUSRCLK TXUSRCLK2} {lappend nets {*}[get_nets -of_objects [get_pins $g/$p]]}
 puts "GT_AUDIT $g [get_property LOC $g] WIDTH=[get_property TX_DATA_WIDTH $g] DIV=[get_property TXOUT_DIV $g]"
 if {[get_property TX_DATA_WIDTH $g]!=40 || [get_property TXOUT_DIV $g]!=2} {error "GT width/div mismatch"}
}
if {[llength [lsort -unique $nets]]!=1} {error "TX user clocks are not shared"}
puts "TX_SHARED_CLOCK_NET [lsort -unique $nets]"
puts "FOUR_GTH_SHARED_CLOCK_STRUCTURE_PASS"
