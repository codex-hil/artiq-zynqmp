// SPDX-License-Identifier: LGPL-3.0-or-later
`timescale 1ns/1ps
module tb_local_reset_retained;
reg pl=0,tx=0,rx=0,run_pl=1,run_tx=1,pl_resetn=0,request=1,abandoned=0;
wire allowed,abandon_ready,control_reset,sys_reset,coordinator_reset;
wire [4:0] domain_ready,target_reset;
always #4 if(run_pl)pl=~pl;
always #7 if(run_tx)tx=~tx;
always #9 rx=~rx;
local_reset_parent dut(.pl_clock(pl),.tx_clock(tx),.rx_clock(rx),.pl_resetn(pl_resetn),.request(request),.abandoned(abandoned),.allowed(allowed),.abandon_ready(abandon_ready),.control_reset(control_reset),.sys_reset(sys_reset),.coordinator_reset(coordinator_reset),.domain_ready(domain_ready),.target_reset(target_reset));
task check;input ok;input [511:0] label;begin if(ok!==1'b1)$fatal(1,"FAIL %s",label);end endtask
integer i,level,stop_tx;
task reopen;begin
 request=0;abandoned=0;
 for(i=0;i<100&&!abandon_ready;i=i+1)#10;
 check(abandon_ready,"fresh abandonment readiness");abandoned=1;
end endtask
task wait_open;begin
 for(i=0;i<200&&!allowed;i=i+1)#10;
 check(allowed&&domain_ready==31&&!sys_reset,"fresh open after all domains");
end endtask
initial begin
 #180;pl_resetn=1;#100;check(!allowed,"initial reset blocks");reopen;wait_open;
 @(negedge tx);run_tx=0;request=1;
 #100;check(sys_reset&&!allowed&&domain_ready==0,"SYS stopped async reset and ready clear");
 reopen;#150;check(sys_reset&&!allowed,"SYS cannot release before resumed edges");
 run_tx=1;wait_open;$display("LOCAL_PARENT_SYS_STOP_PASS");
 for(level=0;level<2;level=level+1)begin
  for(stop_tx=0;stop_tx<2;stop_tx=stop_tx+1)begin
   if(level)@(posedge pl);else @(negedge pl);
   #1;run_pl=0;
   if(stop_tx)begin @(negedge tx);run_tx=0;end
   pl_resetn=0;#50;
   check(control_reset&&sys_reset&&!allowed,"external assertion while control stopped");
   pl_resetn=1;#100;
   check(control_reset&&sys_reset&&!allowed&&target_reset==31,"all resets retained after external release while control stopped");
   run_pl=1;#100;
   check(coordinator_reset&&sys_reset&&!allowed,"coordinator takes reset ownership after control restart");
   check(domain_ready==0,"no stale ready after retained assertion");
   // Old abandonment must not reopen. Establish a fresh explicit reset episode.
   request=1;#60;reopen;
   if(stop_tx)begin #100;check(sys_reset&&!allowed,"TX still needs resumed edges");run_tx=1;end
   wait_open;
   $display("RESET_RETENTION_CASE_PASS control_high=%0d tx_stopped=%0d",level,stop_tx);
  end
 end
 $display("LOCAL_PARENT_RESET_RETENTION_PASS");
 $finish;
end
initial begin #10000;$fatal(1,"timeout");end
endmodule
