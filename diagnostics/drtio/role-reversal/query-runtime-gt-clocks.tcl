# Diagnostic-only known-runtime selector model, matching generated wizard XDC.
# No hardware change, false path, waiver or manual generated clock override.
set gt [get_cells -hierarchical -filter {REF_NAME == GTHE4_CHANNEL}]
if {[llength $gt] != 1} {error "Expected one GT primitive"}
set seen {}
foreach pin [get_pins -of_objects $gt] {
    set name [get_property REF_PIN_NAME $pin]
    if {[regexp {^(TX|RX)OUTCLKSEL\[([0-2])\]$} $name -> direction bit]} {
        set value [expr {$bit == 1 ? 1 : 0}]
        set_case_analysis $value $pin
        lappend seen "$name=$value"
    }
}
if {[llength $seen] != 6} {error "Expected six runtime selector pins, got$seen"}
update_timing
set out [open runtime-clock-audit.tsv w]
puts $out "SELECTORS\t$seen"
foreach clock [get_clocks] {
    puts $out "CLOCK\t$clock\t[get_property PERIOD $clock]\t[get_property SOURCE_PINS $clock]"
}
foreach cell [get_cells -hierarchical -filter {REF_NAME == BUFG_GT}] {
    set pin [get_pins -of_objects $cell -filter {REF_PIN_NAME == O}]
    puts $out "BUFFER\t$cell\t[get_clocks -quiet -of_objects $pin]"
}
close $out
report_clocks -file runtime-clocks.rpt
puts "GT_RUNTIME_CLOCK_QUERY_COMPLETE"
