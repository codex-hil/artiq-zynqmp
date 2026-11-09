// SPDX-License-Identifier: LGPL-3.0-or-later
`timescale 1ns/1ps
module tb_reset_masked_ready;
reg mgmt=0,control=0,a=0,b=0,run_b=1,request=1,abandoned=0;
reg clock_depends_on_reset_release=0;
wire coordinator_reset;
wire admit,abandon_ready,reset_status;
wire [1:0] domain_ready,target_reset;
integer n,b_edges=0,restart_edges;
always @(posedge b)b_edges=b_edges+1;
always #4 mgmt=~mgmt;
always #5 control=~control;
always #7 a=~a;
// Conditional environment model, NOT the vendor GT primitive.
always #9 if(run_b && (!clock_depends_on_reset_release || !coordinator_reset))b=~b;
reset_coordinator dut(.management_clock(mgmt),.control_clock(control),
 .a_clock(a),.b_clock(b),.request(request),.abandoned(abandoned),
 .admit(admit),.abandon_ready(abandon_ready),.reset_status(reset_status),
 .domain_ready(domain_ready),.target_reset(target_reset),.coordinator_reset(coordinator_reset));
task check;
 input ok;input [511:0] label;
 begin if(ok!==1'b1)$fatal(1,"FAIL %s",label);end
endtask
task fresh_abandon;
 begin
  request=0;abandoned=0;
  for(n=0;n<100 && !abandon_ready;n=n+1)#10;
  check(abandon_ready,"fresh abandonment ready");
  abandoned=1;
 end
endtask
task wait_open;
 begin
  for(n=0;n<200 && !admit;n=n+1)#10;
  check(admit && domain_ready==3 && target_reset==0,"fresh domain acks admit");
 end
endtask
initial begin
 #180;check(!admit && reset_status && domain_ready==0 && target_reset==3,"initial reset settled afterGSR");
 // Stop B while reset is held; A/control/management continue.
 run_b=0;
 fresh_abandon;
 #240;check(!admit && domain_ready==1 && target_reset[1],"B stopped blocks release acknowledgement");
 check(!reset_status,"live control entered wait-ready, management status crossed");
 run_b=1;wait_open;
 clock_depends_on_reset_release=1;
 // Stop B after OPEN: reset output asserts asynchronously, but local ready
 // register resets synchronously and retains its old value until a B edge.
 @(negedge b);run_b=0;request=1;
 #160;check(!admit && reset_status && domain_ready==0 && target_reset==3,"masked ready clears while B stopped");
 request=0; // stale abandoned remains high: must not release reset.
 #160;check(!admit && reset_status && target_reset==3,"stale abandonment refused");
 fresh_abandon;
 #200;check(!admit && !reset_status && domain_ready==1 && target_reset[1],"fresh abandonment releases request, B still stopped cannot admit");
 restart_edges=b_edges;
 run_b=1; // Clock returns naturally because coordinator reset has been released.
 wait_open;
 check(b_edges-restart_edges>=6,"fresh ready requires reset release and count after restart");
 $display("MASKED_READY_COORDINATOR_PASS zero-ack-without-clock fresh-restart conditional-wait-removed");
 $finish;
end
initial begin #10000;$fatal(1,"timeout");end
endmodule
