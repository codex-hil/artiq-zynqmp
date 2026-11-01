# SPDX-License-Identifier: LGPL-3.0-or-later
# Parent owns Genesys and plug claims; enumerate only, no target selection.
connect -url tcp:127.0.0.1:3121
set count 0
foreach p [targets -target-properties] {
 if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq "210383B7F02DA"} {
  puts "GENESYS_TARGET $p"
  incr count
 }
}
if {$count == 0} {error "Exact Genesys cable has no visible targets"}
puts "GENESYS_READONLY_TARGET_COUNT $count"
disconnect
