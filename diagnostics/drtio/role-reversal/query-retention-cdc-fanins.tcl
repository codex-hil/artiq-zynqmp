# SPDX-License-Identifier: LGPL-3.0-or-later
# Read-only full combined checkpoint endpoint capture; no design mutation.
set_param general.maxThreads 4
open_checkpoint /srv/nvme-fast-1/vivado-work/genesys-retained-local-cdc-20261112-v1/combined_cdc.dcp
set targets {FDPE_26/PRE FDPE_28/PRE FDPE_30/PRE}
set out [open fanins.tsv w]
set cones {}
foreach name $targets {
 set pin [get_pins -quiet -hierarchical -filter "NAME == \"$name\""]
 if {[llength $pin]!=1} {error "Endpoint not unique: $name"}
 set starts [all_fanin -flat -startpoints_only -to $pin]
 set cells [all_fanin -flat -only_cells -to $pin]
 puts $out "ENDPOINT\t$name\t[join [lsort $starts] ,]\t[join [lsort $cells] ,]"
 foreach cell $cells {dict set cones $cell 1}
}
close $out
set out [open network.tsv w]
foreach cell [lsort [dict keys $cones]] {
 set ref [get_property REF_NAME [get_cells $cell]]
 set init ""
 if {[string match LUT* $ref] || [string match FD* $ref]} {set init [get_property INIT [get_cells $cell]]}
 puts $out "CELL\t$cell\t$ref\t$init"
 foreach pin [get_pins -of_objects [get_cells $cell]] {
  puts $out "PIN\t$pin\t[get_property DIRECTION $pin]\t[join [get_nets -of_objects $pin] ,]"
 }
}
close $out
close_design
puts "RETENTION_FANINS_READONLY_COMPLETE"
