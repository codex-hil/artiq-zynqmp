// SPDX-License-Identifier: LGPL-3.0-or-later
`timescale 1ns/1ps
module tb_reset_five_domains;
reg mgmt=0,ctrl=0,ps=0,tx=0,rx=0,run_tx=1,run_rx=1,dependency=0;
reg request=1,abandoned=0;
wire admit,abandon_ready,reset_status,coordinator_reset;
wire [4:0] domain_ready,target_reset;
integer n,rx_edges=0,restart_edges;
always #4 mgmt=~mgmt;
always #5 ctrl=~ctrl;
always #4 ps=~ps;
always #7 if(run_tx && (!dependency || !coordinator_reset))tx=~tx;
always #9 if(run_rx && (!dependency || !coordinator_reset))rx=~rx;
always @(posedge rx)rx_edges=rx_edges+1;
reset_five_domains dut(.management_clock(mgmt),.control_clock(ctrl),.ps_clock(ps),
 .tx_clock(tx),.rx_clock(rx),.request(request),.abandoned(abandoned),.admit(admit),
 .abandon_ready(abandon_ready),.reset_status(reset_status),
 .coordinator_reset(coordinator_reset),.domain_ready(domain_ready),.target_reset(target_reset));
task check;
 input ok;input [511:0] label;
 begin if(ok!==1'b1)$fatal(1,"FAIL %s",label);end
endtask
task abandon;
 begin
  request=0;abandoned=0;
  for(n=0;n<100&&!abandon_ready;n=n+1)#10;
  check(abandon_ready,"management sees fresh abandonment readiness");abandoned=1;
 end
endtask
task wait_open;
 begin
  for(n=0;n<200&&!admit;n=n+1)#10;
  check(admit&&domain_ready==31&&target_reset==0,"all five fresh domain acks open");
 end
endtask
initial begin
 #180;check(reset_status&&!admit&&domain_ready==0&&target_reset==31,"initial five-domain reset");
 abandon;wait_open;dependency=1;
 @(negedge rx);run_rx=0;run_tx=0;request=1;
 #180;check(reset_status&&!admit&&domain_ready==0&&target_reset==31,"masked clear with TX and RX stopped");
 request=0;#160;check(reset_status&&!admit,"old abandonment cannot release episode");
 abandon;
 #240;check(!reset_status&&!admit&&domain_ready==1&&target_reset==30,"only PS restarted, management/control live");
 run_tx=1;
 #300;check(!admit&&domain_ready==27&&target_reset==4,"PS TX fresh but missing RX prevents admission");
 restart_edges=rx_edges;run_rx=1;wait_open;
 check(rx_edges-restart_edges>=6,"RX reset-release/count sequence fresh");
 $display("FIVE_DOMAIN_MASKED_READY_PASS TX_RX_stopped PS_only TX_only all_fresh_after_RX");
 $finish;
end
initial begin #10000;$fatal(1,"timeout");end
endmodule
