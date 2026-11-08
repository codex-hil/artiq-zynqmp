// SPDX-License-Identifier: LGPL-3.0-or-later
// Original vendor RTL only; ideal input clock, no GT primitive/analog model.
`timescale 1ns/1ps
module tb_powergood_runtime;
reg clk=0, ticking=1, pg=0;
reg [2:0] user_rate=0;
wire [2:0] rate;
wire mode, done;
integer n;
always #2 if(ticking) clk=~clk;
gtwizard_ultrascale_v1_7_22_gthe4_delay_powergood #(
 .C_USER_GTPOWERGOOD_DELAY_EN(1), .C_PCIE_ENABLE(0)) dut (
 .USER_RXPD(2'b00), .USER_GTRXRESET(1'b0), .USER_RXPMARESET(1'b0),
 .USER_RXRATE(user_rate), .USER_RXRATEMODE(1'b0),
 .GT_GTPOWERGOOD(pg), .GT_RXOUTCLKPCS(clk),
 .GT_RXPD(), .GT_GTRXRESET(), .GT_RXPMARESET(),
 .GT_RXRATE(rate), .GT_RXRATEMODE(mode), .USER_GTPOWERGOOD(done));
task check;
 input ok;
 input [255:0] label;
 begin if(ok!==1'b1) $fatal(1,"FAIL %s",label); end
endtask
task step;
 begin @(posedge clk); #0.1; end
endtask
initial begin
 #1; check(rate==1 && mode==1 && done==0,"initial startup");
 repeat(3) step;
 pg=1;
 for(n=0;n<20;n=n+1) begin
  step;
  if(!done) check(rate==1 && mode==1,"startup held");
 end
 check(done && rate==0 && mode==0,"runtime passthrough");
 user_rate=3; #0.1; check(rate==3,"mux passes user not constant");
 user_rate=0;
 @(negedge clk); ticking=0; pg=0; #12;
 check(done && rate==0,"stopped RX retains stale done");
 ticking=1; step;
 check(!done && rate==1 && mode==1,"first RX edge clears stale done");
 pg=1; repeat(20) step;
 check(done && rate==0 && mode==0,"restart returns runtime");
 $display("POWERGOOD_VENDOR_RTL_PASS startup runtime user-change stopped-clock stale-done restart");
 $finish;
end
initial begin #1000; $fatal(1,"timeout"); end
endmodule
