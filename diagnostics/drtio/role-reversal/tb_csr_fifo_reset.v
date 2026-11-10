// SPDX-License-Identifier: LGPL-3.0-or-later
`timescale 1ns/1ps
module tb_csr_fifo_reset;
reg ps=0,tx=0,run_ps=1,run_tx=1,pr=1,tr=1,valid=0,ready=0;
reg [31:0] data=0;wire sr,sv;wire [31:0] sd;wire r0,r1;
always #4 if(run_ps)ps=~ps;
integer phase=0;
initial begin
 if($value$plusargs("PHASE=%d",phase))begin end
 #(phase);forever #7 if(run_tx)tx=~tx;
end
csr_fifo_reset dut(.ps_clock(ps),.tx_clock(tx),.ps_reset(pr),.tx_reset(tr),
.sink_valid(valid),.sink_ready(sr),.sink_data(data),.source_valid(sv),.source_ready(ready),.source_data(sd),.private_reset0(r0),.private_reset1(r1));
task check;input ok;input [511:0] label;begin if(ok!==1'b1)$fatal(1,"FAIL %s",label);end endtask
task send;input [31:0] value;begin
 @(negedge ps);data=value;valid=1;
 @(posedge ps);while(!sr)@(posedge ps);
 @(negedge ps);valid=0;
end endtask
task episode;input stopped;input high;input integer occupancy;
 integer k;begin
 for(k=0;k<occupancy;k=k+1)send(32'hbad00000+k);
 #120;check(sv,"unread stale queue present");
 if(stopped==0)begin
  if(high)@(posedge ps);else @(negedge ps);
  #1;run_ps=0;
 end else begin
  if(high)@(posedge tx);else @(negedge tx);
  #1;run_tx=0;
 end
 check((stopped?tx:ps)==high,"source stopped at requested level");
 pr=1;tr=1;#3;check(r0&&r1,"async assertion while source stopped");
 pr=0;#100;check(r0&&r1,"TX reset retains both private resets");
 tr=0;#100;
 check(stopped ? (!r0&&r1) : (r0&&!r1),"stopped private reset cannot release without edges");
 run_ps=1;run_tx=1;#150;
 check(!r0&&!r1&&!sv,"release on resumed clocks discards entire old queue");
 for(k=0;k<3;k=k+1)send(32'h12340000+k);
 #100;
 for(k=0;k<3;k=k+1)begin
  @(negedge tx);check(sv&&sd==32'h12340000+k,"fresh FIFO order exact under backpressure");
  ready=1;@(posedge tx);@(negedge tx);ready=0;#28;
 end
 #60;check(!sv,"three fresh tokens consumed exactly once");
 $display("FIFO_MATRIX_CASE_PASS phase=%0d stopped=%0d high=%0d occupancy=%0d",phase,stopped,high,occupancy);
end endtask
integer stop_index,level,fill,cases=0;
initial begin #180;pr=0;tr=0;#150;
 for(stop_index=0;stop_index<2;stop_index=stop_index+1)
  for(level=0;level<2;level=level+1)
   for(fill=1;fill<=4;fill=fill+1)begin
    episode(stop_index,level,fill);cases=cases+1;
   end
 check(cases==16,"all sixteen cases executed");
 $display("CSR_COMMON_RESET_FIFO_PASS phase=%0d cases=%0d",phase,cases);$finish;
end
initial begin #100000;$fatal(1,"timeout");end
endmodule
