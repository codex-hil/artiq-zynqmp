// SPDX-License-Identifier: LGPL-3.0-or-later
`timescale 1ns/1ps
module mapped_bench #(parameter CE_BAD=0,AND_BAD=0);
reg pl=0,tx=0,run_pl=1,run_tx=1,rn=0,armed=0;
wire cr,qr,hold_reset,sr;
integer high,stopped,offset,cases=0;
always #4 if(run_pl)pl=~pl;
always #7 if(run_tx)tx=~tx;
mapped_reset #(.MUTATE_CE(CE_BAD),.MUTATE_AND(AND_BAD)) dut(.pl_clock(pl),.tx_clock(tx),.pl_resetn(rn),.raw_reset(1'b0),.control_reset(cr),.coordinator_reset(qr),.retained_request(hold_reset),.sys_reset(sr));
task check;input ok;input [511:0] label;begin if(ok!==1'b1)$fatal(1,"FAIL %s",label);end endtask
always @(negedge cr)begin #0.001;if(armed)check(qr&&hold_reset,"mapped coordinator owns reset at control release");end
initial begin
 #200;rn=1;#150;check(!cr&&!qr&&!sr,"initial discrete release");armed=1;
 for(high=0;high<2;high=high+1)
 for(stopped=0;stopped<2;stopped=stopped+1)
 for(offset=1;offset<=6;offset=offset+1)if(offset==1||offset==3||offset==6)begin
  if(high)@(posedge pl);else @(negedge pl);#1;run_pl=0;
  if(stopped)begin @(negedge tx);run_tx=0;end
  rn=0;#3;check(cr&&hold_reset&&sr,"mapped asynchronous assertion with paused control");
  #(50+offset);rn=1;#60;check(cr&&hold_reset&&sr,"mapped retention after external release");
  run_pl=1;#60;check(!cr&&!qr&&!hold_reset,"coordinator releases after fresh PL edges");
  if(stopped)begin check(sr,"SYS reset cannot release without SYS edges");run_tx=1;end
  #100;check(!sr,"SYS releases after returned edges");
  cases=cases+1;$display("MAPPED_CASE_PASS high=%0d stopped=%0d offset=%0d",high,stopped,offset);
 end
 check(cases==12,"twelve cases executed");$display("MAPPED_RESET_SLICE_PASS cases=%0d",cases);$finish;
end
initial begin #20000;$fatal(1,"timeout");end
endmodule
module tb_mapped_reset;mapped_bench b();endmodule
module tb_mapped_ce_bad;mapped_bench #(.CE_BAD(1)) b();endmodule
module tb_mapped_and_bad;mapped_bench #(.AND_BAD(1)) b();endmodule
