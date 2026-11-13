# SPDX-License-Identifier: LGPL-3.0-or-later
# Read-only primitive slice including combinational PRE and CE drivers.
set_param general.maxThreads 4
open_checkpoint /srv/nvme-fast-1/vivado-work/genesys-retained-local-cdc-20261112-v1/combined_cdc.dcp
set cells {}
foreach name {FDPE_4 FDPE_5 genesysmasterintegration_ingress_outputs_reset_reg FDPE_28 FDPE_29} {
 set cell [get_cells -quiet -hierarchical -filter "NAME == \"$name\""]
 if {[llength $cell]!=1} {error "Primitive not unique $name"}
 dict set cells $cell 1
}
foreach name {FDPE_4/PRE FDPE_28/PRE FDPE_4/D FDPE_28/D FDPE_4/CE FDPE_5/CE genesysmasterintegration_ingress_outputs_reset_reg/CE} {
 set pin [get_pins -quiet -hierarchical -filter "NAME == \"$name\""]
 set drivers [get_pins -of_objects [get_nets -segments -of_objects $pin] -filter {DIRECTION == OUT}]
 if {[llength $drivers]!=1} {error "Driver not unique $name"}
 dict set cells [get_cells -of_objects $drivers] 1
}
set out [open primitives.tsv w]
foreach cell [lsort [dict keys $cells]] {
 set ref [get_property REF_NAME $cell]
 set init ""
 if {[string match FD* $ref] || [string match LUT* $ref]} {set init [get_property INIT $cell]}
 puts $out "CELL\t$cell\t$ref\t$init"
 foreach property [list_property $cell] {
  if {[regexp {^IS_.*_INVERTED$} $property]} {puts $out "PARAM\t$cell\t$property\t[get_property $property $cell]"}
 }
 foreach pin [get_pins -of_objects $cell] {
  puts $out "PIN\t$pin\t[get_property DIRECTION $pin]\t[join [get_nets -of_objects $pin] ,]"
 }
}
close $out
close_design
puts "MAPPED_RESET_PRIMITIVES_READONLY_COMPLETE"
