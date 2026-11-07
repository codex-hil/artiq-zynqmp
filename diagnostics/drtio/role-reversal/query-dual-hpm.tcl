# Isolated PS IP inspection only: no synthesis, implementation or HW connection.
set_param general.maxThreads 4
create_project -force hpm_query ./project -part xczu5ev-sfvc784-1-e
create_bd_design hpm_query
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.5 zynq_ultra_ps_e_0
set ::artiq_variant local-rtio
source ./board.properties.tcl
source ./ps-dual-hpm.properties.tcl
set out [open query.tsv w]
foreach key {PSU__USE__M_AXI_GP0 PSU__USE__M_AXI_GP1 PSU__MAXIGP0__DATA_WIDTH PSU__MAXIGP1__DATA_WIDTH} {
    puts $out "CONFIG\t$key\t[get_property CONFIG.$key [get_bd_cells zynq_ultra_ps_e_0]]"
}
foreach port {M_AXI_HPM0_FPD M_AXI_HPM1_FPD} {
    set pin [get_bd_intf_pins zynq_ultra_ps_e_0/$port]
    if {[llength $pin] != 1} {error "Missing interface $port"}
    foreach property [lsort [list_property $pin]] {
        if {[string match CONFIG.* $property]} {
            puts $out "INTERFACE\t$port\t$property\t[get_property $property $pin]"
        }
    }
}
foreach name {maxihpm0_fpd_aclk maxihpm1_fpd_aclk} {
    set pin [get_bd_pins zynq_ultra_ps_e_0/$name]
    if {[llength $pin] != 1} {error "Missing clock $name"}
    puts $out "CLOCK\t$name\t[get_property DIR $pin]\t[get_property TYPE $pin]"
}
# Actual connected address discovery, not a guessed aperture.
foreach index {0 1} {
    create_bd_cell -type ip -vlnv xilinx.com:ip:axi_bram_ctrl:4.1 probe$index
    set_property -dict [list CONFIG.DATA_WIDTH {32} CONFIG.SINGLE_PORT_BRAM {1}] [get_bd_cells probe$index]
    connect_bd_intf_net [get_bd_intf_pins zynq_ultra_ps_e_0/M_AXI_HPM${index}_FPD] [get_bd_intf_pins probe$index/S_AXI]
}
assign_bd_address
foreach segment [get_bd_addr_segs -hierarchical] {
    puts $out "SEGMENT\t$segment\t[get_property OFFSET $segment]\t[get_property RANGE $segment]"
}
close $out
save_bd_design
write_bd_tcl -force exported-bd.tcl
puts "DUAL_HPM_QUERY_COMPLETE"
