// SPDX-License-Identifier: LGPL-3.0-or-later
// Original vendor helper and AMD BUFG_GT simulation library; ideal source only.
`timescale 1ns/1ps
module tb_userclk_active;
reg src=0, ticking=1, reset=1;
wire usr, usr2, active;
integer edges=0;
always #4 if(ticking) src=~src;
always @(posedge usr2) edges=edges+1;
gtwizard_ultrascale_v1_7_22_gtwiz_userclk_rx #(
 .P_CONTENTS(0), .P_FREQ_RATIO_SOURCE_TO_USRCLK(1),
 .P_FREQ_RATIO_USRCLK_TO_USRCLK2(1)) dut (
 .gtwiz_userclk_rx_srcclk_in(src), .gtwiz_userclk_rx_reset_in(reset),
 .gtwiz_userclk_rx_usrclk_out(usr), .gtwiz_userclk_rx_usrclk2_out(usr2),
 .gtwiz_userclk_rx_active_out(active));
task check;
 input ok;
 input [511:0] label;
 begin if(ok!==1'b1) $fatal(1,"FAIL %s",label); end
endtask
integer held;
initial begin
 // Allow default glbl GSR100ns to finish before testing the helper.
 #120; check(!active,"reset clears active");
 reset=0; #80; check(active,"running source raises active");
 @(negedge src); ticking=0; held=edges;
 #80; check(edges==held,"no output edges during source stop");
 check(active,"source stop retains stale active");
 reset=1; #1; check(!active,"reset clears active without source edge");
 reset=0; #40; check(!active,"release without source edges remains inactive");
 ticking=1; #80; check(active,"restart raises active");
 check(edges>held,"output edges resumed");
 $display("USERCLK_VENDOR_RTL_PASS running stopped-stale asynchronous-reset stopped-release restart");
 $finish;
end
initial begin #1000; $fatal(1,"timeout"); end
endmodule
