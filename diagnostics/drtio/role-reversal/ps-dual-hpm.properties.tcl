# Isolated overlay: source existing board PS properties first with its variant.
# Not adopted by the normal platform; requires exported ports/address review.
set_property -dict [list \
    CONFIG.PSU__USE__M_AXI_GP0 {1} \
    CONFIG.PSU__USE__M_AXI_GP1 {1} \
    CONFIG.PSU__USE__M_AXI_GP2 {0} \
    CONFIG.PSU__MAXIGP0__DATA_WIDTH {32} \
    CONFIG.PSU__MAXIGP1__DATA_WIDTH {32} \
] [get_bd_cells zynq_ultra_ps_e_0]
