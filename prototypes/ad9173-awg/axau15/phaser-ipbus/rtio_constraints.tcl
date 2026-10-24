# Apply after synthesis and clock definition. Never false-path whole domains.
set first {}
foreach n [get_nets -hier -filter {MR_FF == TRUE}] {
 foreach p [get_pins -of_objects $n -filter {DIRECTION == OUT}] {
  set c [get_cells -of_objects $p]
  if {[get_property ASYNC_REG $c] ni {1 TRUE}} {error "MR_FF lacks ASYNC_REG"}
  lappend first {*}[get_pins -of_objects $c -filter {REF_PIN_NAME == D}]
 }
}
if {[llength $first]<30} {error "Missing synchronizers"}
foreach pin $first {
 set src [all_fanin -flat -startpoints_only -to $pin]
 if {[llength $src]} {set_max_delay -datapath_only 6.0 -from $src -to $pin}
}
foreach {source destination expected} {
 *env_config_*reg* *envelope_active_config_reg* 43
 *rtio_event_held_reg* *rtio_event_active_reg* 32
 *rtio_response_held_reg* *rtio_response_active_reg* 8
} {
 set from [get_cells -hier -filter "NAME =~ $source"]
 set to [get_cells -hier -filter "NAME =~ $destination"]
 if {[llength $from]!=$expected || [llength $to]!=$expected} {error "CDC bank mismatch $source $destination: [llength $from]/[llength $to]"}
 set_max_delay -datapath_only 6.0 -from $from -to $to
 set_bus_skew 6.0 -from $from -to $to
}
set from [get_cells -hier -filter {NAME =~ *config_held_reg*}]
set to [get_cells -hier -filter {NAME =~ *generator_config_active_reg* || NAME =~ *generator_clear_reg*}]
if {[llength $from]<643 || [llength $to]<643} {error "DDS CDC bank missing"}
set_max_delay -datapath_only 6.0 -from $from -to $to
set_bus_skew 6.0 -from $from -to $to
