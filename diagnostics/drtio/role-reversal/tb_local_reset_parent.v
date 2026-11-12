// SPDX-License-Identifier: LGPL-3.0-or-later
`timescale 1ns/1ps
module tb_local_reset_parent;
reg pl=0,tx=0,rx=0,run_pl=1,run_tx=1,pl_resetn=0,request=1,abandoned=0;
wire allowed,abandon_ready,control_reset,sys_reset,coordinator_reset;
wire [4:0] domain_ready,target_reset;
always #4 if(run_pl)pl=~pl;
always #7 if(run_tx)tx=~tx;
always #9 rx=~rx;
local_reset_parent dut(.pl_clock(pl),.tx_clock(tx),.rx_clock(rx),.pl_resetn(pl_resetn),.request(request),.abandoned(abandoned),.allowed(allowed),.abandon_ready(abandon_ready),.control_reset(control_reset),.sys_reset(sys_reset),.coordinator_reset(coordinator_reset),.domain_ready(domain_ready),.target_reset(target_reset));
task check;input ok;input [511:0] label;begin if(ok!==1'b1)$fatal(1,"FAIL %s",label);end endtask
integer i;
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
 // Deliberately challenge the always-live control assumption. Reproduce
 // the conditional reopening hazard, do not treat it as qualified recovery.
 @(negedge pl);run_pl=0;pl_resetn=0;
 #50;check(control_reset&&sys_reset&&!allowed,"external assert with control stopped");
 pl_resetn=1;#80;
 check(control_reset,"control reset remains until PL edges return");
 check(!coordinator_reset&&!sys_reset&&allowed,"conditional stale admit reopening reproduced");
 $display("LOCAL_PARENT_CONTROL_STOP_EXTERNAL_RESET_REOPEN_COUNTEREXAMPLE");
 $finish;
end
initial begin #10000;$fatal(1,"timeout");end
endmodule
