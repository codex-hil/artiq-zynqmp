open_checkpoint routed.dcp
set held [get_cells -hier -regexp {^payload_scan/core/held_reg\[[0-9]+\]}]
set amp [get_cells -hier -regexp {^payload_scan/core/amplitude_reg\[[0-9]+\]}]
if {[llength $held]!=16 || [llength $amp]!=16} {error "Mailbox width"}
report_timing -from $held -to $amp -max_paths 16 -file payload-timing.rpt
report_bus_skew -file payload-skew.rpt
set paths [get_timing_paths -from $held -to $amp -max_paths 16]
if {[llength $paths]!=16} {error "Not all payload bits timed"}
foreach p $paths {
 if {[get_property SLACK $p]<0 || [get_property REQUIREMENT $p]>6.001} {error "Payload bus exceeds CDC budget"}
}
puts "PAYLOAD_16_BITS_BOUNDED_AT_6NS_PASS"
