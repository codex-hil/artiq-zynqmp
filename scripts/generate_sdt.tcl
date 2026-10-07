# Run with Vivado/bin/sdtgen generate_sdt.tcl XSA OUTPUT USER_DTS
if {[llength $argv] != 3} {error "Require XSA OUTPUT USER_DTS"}
lassign $argv xsa output user_dts
set_dt_param -dir $output -xsa $xsa -include_dts $user_dts
generate_sdt
