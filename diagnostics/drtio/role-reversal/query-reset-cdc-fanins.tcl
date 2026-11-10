# Read-only post-synthesis topology capture, exact two checkpoint inputs.
set_param general.maxThreads 4
proc capture {path label masked} {
 open_checkpoint $path
 set out [open "$label-network.tsv" w]
 foreach cell [lsort [get_cells -hierarchical -filter {IS_PRIMITIVE == 1}]] {
  set ref [get_property REF_NAME $cell]
  set init ""
  if {[string match LUT* $ref] || [string match FD* $ref]} {set init [get_property INIT $cell]}
  puts $out "CELL\t$cell\t$ref\t$init"
  foreach pin [get_pins -of_objects $cell] {
   set nets [get_nets -of_objects $pin]
   if {[llength $nets]>1} {error "Ambiguous pin net: $pin"}
   puts $out "PIN\t$pin\t[get_property DIRECTION $pin]\t[join $nets ,]"
  }
 }
 foreach port [get_ports] {
  set nets [get_nets -of_objects $port]
  if {[llength $nets]>1} {error "Ambiguous port net"}
  puts $out "PORT\t$port\t[get_property DIRECTION $port]\t[join $nets ,]"
 }
 close $out
 set out [open "$label-fanins.tsv" w]
 set targets {}
 for {set i 0} {$i<5} {incr i} {
  set cell "xilinxmultiregimpl${i}0_reg"
  if {$masked} {set cell "xilinxmultiregimpl${i}_$cell"}
  lappend targets "$cell/D" "$cell/R"
 }
 foreach index {7 8 9} {lappend targets "xilinxmultiregimpl${index}0_reg/D"}
 foreach cell {FDPE FDPE_2 FDPE_4 FDPE_6 FDPE_8} {lappend targets "$cell/PRE"}
 foreach name $targets {
  set pin [get_pins -quiet $name]
  if {[llength $pin]!=1} {error "Endpoint not unique: $name"}
  set starts [all_fanin -flat -startpoints_only -to $pin]
  set cells [all_fanin -flat -only_cells -to $pin]
  puts $out "ENDPOINT\t$name\t[join [lsort $starts] ,]\t[join [lsort $cells] ,]"
 }
 close $out
 close_design
}
capture /srv/nvme-fast-1/vivado-work/genesys-reset-original-five-cdc-20261110-v1/reset_cdc.dcp original 0
capture /srv/nvme-fast-1/vivado-work/genesys-reset-five-cdc-20261110-v1/reset_cdc.dcp masked 1
puts "RESET_CDC_FANIN_READONLY_CAPTURE_COMPLETE"
