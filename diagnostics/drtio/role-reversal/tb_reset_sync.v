// SPDX-License-Identifier: LGPL-3.0-or-later
`timescale 1ns/1ps
module tb_reset_sync;
reg clk=0,request=1;
wire reset;
reset_sync dut(.source_clk(clk),.reset_request(request),.reset_out(reset));
task check;
 input ok;input [511:0] label;
 begin if(ok!==1'b1)$fatal(1,"FAIL %s",label);end
endtask
task pulse;
 begin clk=1;#2;clk=0;#2;end
endtask
initial begin
 #120;check(reset==1,"GSR completed, request held, clock stopped low");
 request=0;#16;check(reset==1,"release with no edge remains asserted");
 pulse;check(reset==1,"first edge retains reset");
 pulse;check(reset==0,"second edge releases reset");
 #16;check(reset==0,"stopped clock alone does not assert reset");
 request=1;#1;check(reset==1,"async assertion while clock stopped low");
 request=0;#16;check(reset==1,"deassert request alone cannot release");
 pulse;check(reset==1,"restart first edge");
 pulse;check(reset==0,"restart second edge");
 clk=1;#2;request=1;#1;check(reset==1,"async assertion while clock stopped high");
 request=0;#16;check(reset==1,"stopped high release remains held");
 clk=0;#2;pulse;check(reset==1,"high-stop first resumed rising edge");
 pulse;check(reset==0,"high-stop second resumed rising edge");
 $display("RESET_FDPE_GSR_PASS stopped-low stopped-high async-assert two-edge-release");
 $finish;
end
initial begin #1000;$fatal(1,"timeout");end
endmodule
