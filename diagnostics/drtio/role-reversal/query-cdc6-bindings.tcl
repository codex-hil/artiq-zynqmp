# SPDX-License-Identifier: LGPL-3.0-or-later
# Exact source Q -> stage0 D and stage0 Q -> stage1 D bindings, no mutation.
set_param general.maxThreads 4
open_checkpoint /srv/nvme-fast-1/vivado-work/genesys-retained-local-cdc-20261112-v1/combined_cdc.dcp
set input [open endpoints.tsv r]
set out [open bindings.tsv w]
while {[gets $input line]>=0} {
 lassign [split $line "\t"] source first second
 set pins {}
 foreach name [list $source $first $second] {
  set p [get_pins -quiet -hierarchical -filter "NAME == \"$name\""]
  if {[llength $p]!=1} {error "Pin not unique: $name"}
  lappend pins $p
 }
 lassign $pins s d0 d1
 set c0 [get_cells -of_objects $d0]
 set q0 [get_pins -of_objects $c0 -filter {REF_PIN_NAME == Q}]
 set c1 [get_cells -of_objects $d1]
 set sn [get_nets -of_objects $s]
 set dn [get_nets -of_objects $d0]
 set qn [get_nets -of_objects $q0]
 set nextn [get_nets -of_objects $d1]
 if {[llength $sn]!=1 || $sn ne $dn || [llength $qn]!=1 || $qn ne $nextn} {error "Not direct register chain: $line"}
 puts $out "$source\t$first\t$second\t$sn\t$qn\t[get_property REF_NAME [get_cells -of_objects $s]]\t[get_property REF_NAME $c0]\t[get_property REF_NAME $c1]\t[get_property ASYNC_REG $c0]\t[get_property ASYNC_REG $c1]"
}
close $input
close $out
close_design
puts "CDC6_DIRECT_TWO_STAGE_BINDINGS_COMPLETE"
