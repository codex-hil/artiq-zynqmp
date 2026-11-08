# Source in isolated elaborated design. No false paths or CDC exceptions.
proc require_one {objects label} {
    if {[llength $objects] != 1} {error "$label: expected1 got[llength $objects]"}
    return $objects
}
create_clock -name ps_management -period 8.000 [require_one [get_ports pl_clk0] ps_clock_port]
create_clock -name gt_reference -period 6.400 [require_one [get_ports ref_p] reference_port]
update_timing
set out [open clock-audit.tsv w]
foreach clock [get_clocks] {
    puts $out "CLOCK\t$clock\t[get_property PERIOD $clock]\t[get_property SOURCE_PINS $clock]"
}
foreach cell [get_cells -hierarchical -filter {REF_NAME == BUFG_GT}] {
    set pin [get_pins -of_objects $cell -filter {REF_PIN_NAME == O}]
    puts $out "BUFFER\t$cell\t[get_clocks -quiet -of_objects $pin]"
}
close $out
report_clocks -file clocks.rpt
puts "MASTER_PHY_CLOCK_QUERY_COMPLETE"
