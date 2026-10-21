create_project -in_memory -part xczu5ev-sfvc784-1-e
read_ip {ip/platform_zynq_ultra_ps_e_0_0/platform_zynq_ultra_ps_e_0_0.xci}
upgrade_ip [get_ips platform_zynq_ultra_ps_e_0_0]
generate_target all [get_ips platform_zynq_ultra_ps_e_0_0]
quit
