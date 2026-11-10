// SPDX-License-Identifier: LGPL-3.0-or-later
`timescale 1ns/1ps
module tb_csr_fifo_reset;
reg ps=0,tx=0,run_ps=1,run_tx=1,pr=1,tr=1,valid=0,ready=0;
reg [31:0] data=0;wire sr,sv;wire [31:0] sd;wire r0,r1;
always #4 if(run_ps)ps=~ps;
always #7 if(run_tx)tx=~tx;
csr_fifo_reset dut(.ps_clock(ps),.tx_clock(tx),.ps_reset(pr),.tx_reset(tr),
.sink_valid(valid),.sink_ready(sr),.sink_data(data),.source_valid(sv),.source_ready(ready),.source_data(sd),.private_reset0(r0),.private_reset1(r1));
task check;input ok;input [511:0] label;begin if(ok!==1'b1)$fatal(1,"FAIL %s",label);end endtask
task send;input [31:0] value;begin
 @(negedge ps);data=value;valid=1;
 @(posedge ps);while(!sr)@(posedge ps);
 @(negedge ps);valid=0;
end endtask
task episode;input stopped;begin
 // Queue an unread token which coordinated reset must discard.
 send(32'hbad00000+stopped);#120;check(sv,"stale token queued");
 if(stopped==0)begin @(negedge ps);run_ps=0;end
 else begin @(negedge tx);run_tx=0;end
 pr=1;tr=1;#3;check(r0&&r1,"asynchronous common assertion with source stopped");
 // One side releases first: other reset must hold BOTH private resets.
 pr=0;#100;check(r0&&r1,"TX reset retains common assertion");
 run_ps=1;run_tx=1;#30;tr=0;
 #150;check(!r0&&!r1,"both private resets released on resumed clocks");
 check(!sv,"stale token discarded after coordinated reset");
 send(32'h12340000+stopped);#100;check(sv&&sd==32'h12340000+stopped,"fresh payload exact");
 @(negedge tx);ready=1;@(posedge tx);@(negedge tx);ready=0;
 #60;check(!sv,"fresh token consumed once");
end endtask
initial begin #180;pr=0;tr=0;#150;episode(0);episode(1);
 $display("CSR_COMMON_RESET_FIFO_PASS stoppedPS stoppedTX staleDiscard freshTransfer");$finish;end
initial begin #10000;$fatal(1,"timeout");end
endmodule
