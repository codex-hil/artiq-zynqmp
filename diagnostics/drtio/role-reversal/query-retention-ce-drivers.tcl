# SPDX-License-Identifier: LGPL-3.0-or-later
# Read-only exact CE pin driver capture; names alone are not constants.
set_param general.maxThreads 4
open_checkpoint /srv/nvme-fast-1/vivado-work/genesys-retained-local-cdc-20261112-v1/combined_cdc.dcp
set out [open ce-drivers.tsv w]
foreach name {genesysmasterintegration_ingress_outputs_reset_reg/CE FDPE_4/CE FDPE_5/CE} {
 set pin [get_pins -quiet -hierarchical -filter "NAME == \"$name\""]
 if {[llength $pin]!=1} {error "CE pin not unique: $name"}
 set nets [get_nets -segments -of_objects $pin]
 set drivers [get_pins -of_objects $nets -filter {DIRECTION == OUT}]
 if {[llength $drivers]!=1} {error "CE driver not unique: $name"}
 set cell [get_cells -of_objects $drivers]
 if {[get_property REF_NAME $cell] ne "VCC"} {error "CE driver is not VCC: $name"}
 puts $out "$name\t[join $nets ,]\t$drivers\t$cell\t[get_property REF_NAME $cell]"
}
close $out
close_design
puts "RETENTION_CE_VCC_DRIVERS_READONLY_COMPLETE"
