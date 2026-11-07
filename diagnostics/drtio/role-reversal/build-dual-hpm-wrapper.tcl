# Isolated PS validation/HDL export, not synthesis/implementation or hardware.
set_param general.maxThreads 4
create_project -force dual_hpm_wrapper ./project -part xczu5ev-sfvc784-1-e
create_bd_design dual_hpm
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.5 zynq_ultra_ps_e_0
set ::artiq_variant local-rtio
source ./board.properties.tcl
source ./ps-dual-hpm.properties.tcl
set out [open pins.tsv w]
foreach pin [get_bd_pins zynq_ultra_ps_e_0/*] {
    puts $out "[get_property NAME $pin]\t[get_property DIR $pin]\t[get_property LEFT $pin]\t[get_property RIGHT $pin]"
    if {![get_property INTF $pin]} {make_bd_pins_external $pin}
}
close $out
foreach pin [get_bd_intf_pins zynq_ultra_ps_e_0/*] {make_bd_intf_pins_external $pin}
foreach port [get_bd_ports] {
    if {[get_property TYPE $port] eq "clk" && [get_property DIR $port] eq "I"} {
        set_property CONFIG.FREQ_HZ 125000000 $port
    }
}
assign_bd_address -offset 0xa0000000 -range 0x20000 -target_address_space [get_bd_addr_spaces zynq_ultra_ps_e_0/Data] [get_bd_addr_segs M_AXI_HPM0_FPD_0/Reg]
assign_bd_address -offset 0xb0000000 -range 0x1000 -target_address_space [get_bd_addr_spaces zynq_ultra_ps_e_0/Data] [get_bd_addr_segs M_AXI_HPM1_FPD_0/Reg]
validate_bd_design
save_bd_design
write_bd_tcl -force exported-bd.tcl
set bd [get_files dual_hpm.bd]
generate_target all $bd
set wrappers [make_wrapper -files $bd -top -import]
set out [open wrappers.txt w]
foreach wrapper $wrappers {puts $out $wrapper}
close $out
puts "DUAL_HPM_VALIDATED_WRAPPER_COMPLETE"
