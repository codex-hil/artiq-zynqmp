# Vivado 2025.2: diagnostic raw 20-bit PHY, not a complete DRTIO satellite.
# Usage: vivado -mode batch -source build_phy.tcl -tclargs OUTPUT [REFCLK_MHZ]
if {[llength $argv] < 1 || [llength $argv] > 2} {error "Require OUTPUT ?REFCLK_MHZ?"}
set output [file normalize [lindex $argv 0]]
set refclk 125
if {[llength $argv] == 2} {set refclk [lindex $argv 1]}
if {$refclk ni {125 156.25}} {error "Diagnostic profiles support 125 or 156.25 MHz"}
file mkdir $output
create_project drtio_phy $output/project -part xczu5ev-sfvc784-1-e -force
create_ip -name gtwizard_ultrascale -vendor xilinx.com -library ip -version 1.7 -module_name drtio_gth
set ip [get_ips drtio_gth]
set_property -dict [list \
 CONFIG.CHANNEL_ENABLE {X0Y7} \
 CONFIG.TX_MASTER_CHANNEL {X0Y7} CONFIG.RX_MASTER_CHANNEL {X0Y7} \
 CONFIG.TX_LINE_RATE {2.5} CONFIG.RX_LINE_RATE {2.5} \
 CONFIG.TX_REFCLK_FREQUENCY $refclk CONFIG.RX_REFCLK_FREQUENCY $refclk \
 CONFIG.TX_PLL_TYPE {CPLL} CONFIG.RX_PLL_TYPE {CPLL} \
 CONFIG.TX_DATA_ENCODING {RAW} CONFIG.RX_DATA_DECODING {RAW} \
 CONFIG.TX_USER_DATA_WIDTH {20} CONFIG.RX_USER_DATA_WIDTH {20} \
 CONFIG.TX_INT_DATA_WIDTH {20} CONFIG.RX_INT_DATA_WIDTH {20} \
 CONFIG.FREERUN_FREQUENCY {125} \
 CONFIG.TX_BUFFER_MODE {1} CONFIG.RX_BUFFER_MODE {1} \
 CONFIG.RX_OUTCLK_SOURCE {RXOUTCLKPMA} \
 CONFIG.TX_REFCLK_SOURCE {X0Y7 clk0} CONFIG.RX_REFCLK_SOURCE {X0Y7 clk0} \
 CONFIG.ENABLE_OPTIONAL_PORTS {rxoutclk_out txoutclk_out cplllock_out rxresetdone_out txresetdone_out rxprbssel_in rxprbserr_out txprbssel_in loopback_in} \
 ] $ip
set config [open $output/configuration.txt w]
foreach p [lsort [list_property $ip]] {
 if {[string match CONFIG.* $p]} {puts $config "$p=[get_property $p $ip]"}
}
close $config
generate_target all $ip
create_ip_run $ip
set run_name drtio_gth_synth_1
launch_runs $run_name -jobs 2
wait_on_run $run_name
if {[get_property PROGRESS [get_runs $run_name]] ne "100%"} {
 error "PHY synthesis incomplete: [get_property STATUS [get_runs $run_name]]"
}
puts "TEST GTHE4_PHY_OOC PASS refclk_MHz=$refclk linerate_Gbps=2.5 width=20"
puts "TEST DRTIO_HARDWARE NOT_RUN; IP build is not link/timing proof"
close_project
