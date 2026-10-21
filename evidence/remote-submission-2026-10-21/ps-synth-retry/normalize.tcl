create_project -force -name normalize -part xczu5ev-sfvc784-1-e
read_ip {ip/platform_zynq_ultra_ps_e_0_0/platform_zynq_ultra_ps_e_0_0.xci}
upgrade_ip [get_ips platform_zynq_ultra_ps_e_0_0]
generate_target all [get_ips platform_zynq_ultra_ps_e_0_0]
create_ip_run [get_ips platform_zynq_ultra_ps_e_0_0]
launch_runs platform_zynq_ultra_ps_e_0_0_synth_1 -jobs 2
wait_on_run platform_zynq_ultra_ps_e_0_0_synth_1
if {[get_property PROGRESS [get_runs platform_zynq_ultra_ps_e_0_0_synth_1]] ne "100%"} {error "PS IP synthesis failed"}
quit
