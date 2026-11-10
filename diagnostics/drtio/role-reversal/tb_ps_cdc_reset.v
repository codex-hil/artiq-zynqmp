// SPDX-License-Identifier: LGPL-3.0-or-later
`timescale 1ns/1ps
module tb_ps_cdc_reset;
reg ps=0,tx=0,run_ps=1,run_tx=1,pr=1,tr=1;
integer phase=0,stop_index,level,mode_index,fill,cases=0;
wire [9:0] private_resets;
always #4 if(run_ps)ps=~ps;
initial begin if($value$plusargs("PHASE=%d",phase))begin end
 #(phase);forever #7 if(run_tx)tx=~tx;end
reg [44:0] aw_input=0;wire [44:0] aw_output;
reg aw_sink_valid=0,aw_source_ready=0;wire aw_sink_ready,aw_source_valid;
reg [37:0] w_input=0;wire [37:0] w_output;
reg w_sink_valid=0,w_source_ready=0;wire w_sink_ready,w_source_valid;
reg [3:0] b_input=0;wire [3:0] b_output;
reg b_sink_valid=0,b_source_ready=0;wire b_sink_ready,b_source_valid;
reg [44:0] ar_input=0;wire [44:0] ar_output;
reg ar_sink_valid=0,ar_source_ready=0;wire ar_sink_ready,ar_source_valid;
reg [35:0] r_input=0;wire [35:0] r_output;
reg r_sink_valid=0,r_source_ready=0;wire r_sink_ready,r_source_valid;
ps_cdc_reset dut(.ps_clock(ps),.tx_clock(tx),.ps_reset(pr),.tx_reset(tr),.private_resets(private_resets),.aw_input(aw_input),.aw_output(aw_output),.aw_sink_valid(aw_sink_valid),.aw_sink_ready(aw_sink_ready),.aw_source_valid(aw_source_valid),.aw_source_ready(aw_source_ready),.w_input(w_input),.w_output(w_output),.w_sink_valid(w_sink_valid),.w_sink_ready(w_sink_ready),.w_source_valid(w_source_valid),.w_source_ready(w_source_ready),.b_input(b_input),.b_output(b_output),.b_sink_valid(b_sink_valid),.b_sink_ready(b_sink_ready),.b_source_valid(b_source_valid),.b_source_ready(b_source_ready),.ar_input(ar_input),.ar_output(ar_output),.ar_sink_valid(ar_sink_valid),.ar_sink_ready(ar_sink_ready),.ar_source_valid(ar_source_valid),.ar_source_ready(ar_source_ready),.r_input(r_input),.r_output(r_output),.r_sink_valid(r_sink_valid),.r_sink_ready(r_sink_ready),.r_source_valid(r_source_valid),.r_source_ready(r_source_ready));
task check;input ok;input [511:0] label;begin if(ok!==1'b1)$fatal(1,"FAIL %s",label);end endtask
task send_aw;input [44:0] value;begin
 @(negedge ps);aw_input=value;aw_sink_valid=1;
 @(posedge ps);while(!aw_sink_ready)@(posedge ps);
 @(negedge ps);aw_sink_valid=0;
end endtask
 task receive_aw;input [44:0] value;begin
 @(negedge tx);check(aw_source_valid && aw_output===value,"aw packed metadata/payload exact");
 aw_source_ready=1;@(posedge tx);@(negedge tx);aw_source_ready=0;
end endtask
task send_w;input [37:0] value;begin
 @(negedge ps);w_input=value;w_sink_valid=1;
 @(posedge ps);while(!w_sink_ready)@(posedge ps);
 @(negedge ps);w_sink_valid=0;
end endtask
 task receive_w;input [37:0] value;begin
 @(negedge tx);check(w_source_valid && w_output===value,"w packed metadata/payload exact");
 w_source_ready=1;@(posedge tx);@(negedge tx);w_source_ready=0;
end endtask
task send_b;input [3:0] value;begin
 @(negedge tx);b_input=value;b_sink_valid=1;
 @(posedge tx);while(!b_sink_ready)@(posedge tx);
 @(negedge tx);b_sink_valid=0;
end endtask
 task receive_b;input [3:0] value;begin
 @(negedge ps);check(b_source_valid && b_output===value,"b packed metadata/payload exact");
 b_source_ready=1;@(posedge ps);@(negedge ps);b_source_ready=0;
end endtask
task send_ar;input [44:0] value;begin
 @(negedge ps);ar_input=value;ar_sink_valid=1;
 @(posedge ps);while(!ar_sink_ready)@(posedge ps);
 @(negedge ps);ar_sink_valid=0;
end endtask
 task receive_ar;input [44:0] value;begin
 @(negedge tx);check(ar_source_valid && ar_output===value,"ar packed metadata/payload exact");
 ar_source_ready=1;@(posedge tx);@(negedge tx);ar_source_ready=0;
end endtask
task send_r;input [35:0] value;begin
 @(negedge tx);r_input=value;r_sink_valid=1;
 @(posedge tx);while(!r_sink_ready)@(posedge tx);
 @(negedge tx);r_sink_valid=0;
end endtask
 task receive_r;input [35:0] value;begin
 @(negedge ps);check(r_source_valid && r_output===value,"r packed metadata/payload exact");
 r_source_ready=1;@(posedge ps);@(negedge ps);r_source_ready=0;
end endtask
task episode;input stopped;input high;input integer mode;input integer occupancy;
integer k;begin
for(k=0;k<occupancy;k=k+1)begin
 if(mode!=2)send_aw('h155555555550+k);
 if(mode!=1)send_w('h155555555550+k);
 if(mode==0)begin send_b(k);send_ar('h155555555550+k);send_r('h155555555550+k);end
end
#120;
check(aw_source_valid==(mode!=2) && w_source_valid==(mode!=1),"expected independent stale AW/W queues");
check(b_source_valid==(mode==0) && ar_source_valid==(mode==0) && r_source_valid==(mode==0),"expected response/read queues");
if(occupancy==4)begin
 if(mode!=2)check(!aw_sink_ready,"AW full backpressure");
 if(mode!=1)check(!w_sink_ready,"W full backpressure");
 if(mode==0)check(!b_sink_ready&&!ar_sink_ready&&!r_sink_ready,"response/read full backpressure");
end
if(stopped==0)begin if(high)@(posedge ps);else @(negedge ps);#1;run_ps=0;end
else begin if(high)@(posedge tx);else @(negedge tx);#1;run_tx=0;end
pr=1;tr=1;#3;check(private_resets==1023,"all ten resets assert asynchronously");
pr=0;#100;check(private_resets==1023,"held TX reset retains all pairs");
tr=0;#100;check(private_resets!=0,"stopped clock prevents full release");
run_ps=1;run_tx=1;#150;check(private_resets==0,"all ten release after restart");
check(!aw_source_valid && !w_source_valid && !b_source_valid && !ar_source_valid && !r_source_valid,"all five stale queues discarded");
// Fresh four-entry queues use different values from discarded tokens.
for(k=0;k<4;k=k+1)begin
 if(mode==2)begin
  send_w('h1aaaaaaaaaa0+k);
  if(k==0)begin #100;check(w_source_valid&&!aw_source_valid,"fresh W precedes AW independently");end
  send_aw('h1aaaaaaaaaa0+k);
 end else begin
  send_aw('h1aaaaaaaaaa0+k);
  if(k==0)begin #100;check(aw_source_valid&&!w_source_valid,"fresh AW precedes W independently");end
  send_w('h1aaaaaaaaaa0+k);
 end
 send_b(8+k);send_ar('h1aaaaaaaaaa0+k);send_r('h1aaaaaaaaaa0+k);
end
#100;check(!aw_sink_ready&&!w_sink_ready&&!b_sink_ready&&!ar_sink_ready&&!r_sink_ready,"all fresh queues full");
for(k=0;k<4;k=k+1)begin
 receive_aw('h1aaaaaaaaaa0+k);#14;
 receive_w('h1aaaaaaaaaa0+k);#28;
 receive_b(8+k);#16;
 receive_ar('h1aaaaaaaaaa0+k);#42;
 receive_r('h1aaaaaaaaaa0+k);#24;
end
#100;check(!aw_source_valid && !w_source_valid && !b_source_valid && !ar_source_valid && !r_source_valid,"all fresh tokens consumed once");
$display("PSCDC_CASE_PASS phase=%0d stopped=%0d high=%0d mode=%0d occupancy=%0d",phase,stopped,high,mode,occupancy);
end endtask
initial begin #180;pr=0;tr=0;#150;
for(stop_index=0;stop_index<2;stop_index=stop_index+1)
 for(level=0;level<2;level=level+1)
  for(mode_index=0;mode_index<3;mode_index=mode_index+1)
   for(fill=1;fill<=4;fill=fill+1)begin episode(stop_index,level,mode_index,fill);cases=cases+1;end
check(cases==48,"forty-eight cases executed");
$display("PSCDC_FIVE_CHANNEL_PASS phase=%0d cases=%0d",phase,cases);$finish;end
initial begin #300000;$fatal(1,"timeout");end
endmodule
