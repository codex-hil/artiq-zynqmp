# Candidate mapping from the hash-pinned 44-page AXAU15 manual.
foreach {port pin} {sys_p T24 sys_n U24 sck N21 mosi N22 miso R25 cs_dac R26 cs_clock P25 spi_en P26} {
    set_property PACKAGE_PIN $pin [get_ports $port]
}
set_property IOSTANDARD LVDS [get_ports {sys_p sys_n}]
set_property IOSTANDARD LVCMOS18 [get_ports {sck mosi miso cs_dac cs_clock spi_en}]
set_property SLEW SLOW [get_ports {sck mosi cs_dac cs_clock}]
create_clock -name system_200 -period 5.000 [get_ports sys_p]
if {[llength [get_ports -quiet ref_p]]} {
    foreach {port pin} {ref_p V7 ref_n V6 tx0_p AA5 tx0_n AA4 tx1_p W5 tx1_n W4 tx2_p U5 tx2_n U4 tx3_p R5 tx3_n R4 sync0_p V24 sync0_n W24 sync1_p N24 sync1_n P24} {
        set_property PACKAGE_PIN $pin [get_ports $port]
    }
    set_property IOSTANDARD LVDS [get_ports {sync0_p sync0_n sync1_p sync1_n}]
    create_clock -name mgt_reference -period 4.069010417 [get_ports ref_p]
}
set_property BITSTREAM.CONFIG.UNUSEDPIN PULLNONE [current_design]
# Intentionally no blanket CDC false paths and no bitstream command.
# Physical JTAG mailbox bundled-data and IO timing constraints still need review.
