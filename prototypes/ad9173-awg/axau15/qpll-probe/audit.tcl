open_checkpoint routed.dcp
set q [get_cells -hier -filter {REF_NAME == GTHE4_COMMON}]
set r [get_cells -hier -filter {REF_NAME == IBUFDS_GTE4}]
if {[llength $q]!=1 || [llength $r]!=1} {error "Unexpected GT primitive count"}
foreach c [concat $q $r] {puts "AUDIT_CELL $c LOC=[get_property LOC $c]"}
if {[get_property LOC $q] ne "GTHE4_COMMON_X0Y1" || [get_property LOC $r] ne "GTHE4_COMMON_X0Y1"} {error "QPLL and reference must share bank225 site"}
foreach p {QPLL1_FBDIV QPLL1_REFCLK_DIV} {puts "AUDIT_QPLL $p=[get_property $p $q]"}
report_timing -from [get_pins -hier -filter {REF_PIN_NAME == QPLL1LOCK}] -to [get_pins {lock_sync_reg[0]/D}] -file lock-cdc.rpt
if {[get_property QPLL1_FBDIV $q]!=100 || [get_property QPLL1_REFCLK_DIV $q]!=2} {error "QPLL ratio mismatch"}
puts "QPLL_ROUTED_STRUCTURE_AUDIT_PASS"
