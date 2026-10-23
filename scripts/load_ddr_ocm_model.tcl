# SPDX-License-Identifier: LGPL-3.0-or-later
# Library: caller holds Genesys lease, selected CPU0 is halted at prior observer.
source [file join [file dirname [info script]] load_el3_exception_observer.tcl]
namespace eval ddr_model {
 proc run {elf} {
  fsbl_entry::selected_halted
  set samples [fsbl_entry::observe_pair 0xfffc8834]
  set before [lindex $samples 0]
  if {([dict get $before cpsr] & 31) != 13 ||
      ([dict get $before sctlr_el3] & 0x1005) != 0 ||
      ([dict get $before daif] & 0x2c0) != 0x2c0 ||
      ([dict get $before mpidr_el1] & 255) != 0} {error "Model entry not admitted"}
  dow $elf
  exception_observer::unchanged_controls $before
  if {[fsbl_entry::register pc] != 0xfffc8800} {error "Model entry mismatch"}
  rwr sys 12 vbar_el3 0xfffc8000
  if {[fsbl_entry::register {sys 12 vbar_el3}] != 0xfffc8000} {error "Model VBAR mismatch"}
  exception_observer::unchanged_controls $before
  con
  after 100
  exception_observer::halt
  puts "DDR_MODEL_BEGIN"
  puts "DDR_MODEL_PC [fsbl_entry::register pc]"
  foreach name {x0 x14 x15 x16 x17 x18 x19 x20 x21} {
   puts "DDR_MODEL_REG $name [fsbl_entry::register $name]"
  }
  # Fixed image layout, checked against linker symbols by Python preflight.
  for {set i 0} {$i < 12} {incr i} {
   set address [expr {0xfffc8cf0+4*$i}]
   puts [format "DDR_MODEL_REPORT %d 0x%08x" $i [mrd -value $address]]
  }
  puts [format "DDR_MODEL_RESULT 0x%08x" [mrd -value 0xfffc8d20]]
  puts "DDR_MODEL_END"
 }
}
