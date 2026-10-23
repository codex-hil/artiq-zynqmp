`timescale 1ns/1ps
// Logic-only models: this does NOT simulate analog QPLL lock or vendor timing.
module IBUFDS(input I,IB,output O);assign O=I;endmodule
module BUFGCE_DIV #(parameter BUFGCE_DIVIDE=2)(input I,CE,CLR,output reg O=0);
always @(posedge I) if(CLR) O<=0; else if(CE) O<=~O; endmodule
module IBUFDS_GTE4 #(parameter REFCLK_HROW_CK_SEL=1)(input I,IB,CEB,output O,output reg ODIV2=0);
assign O=I; always @(posedge I) if(!CEB) ODIV2<=~ODIV2; endmodule
module BUFG_GT(input I,CE,CEMASK,CLR,CLRMASK,input [2:0] DIV,output O);assign O=I;endmodule
module BSCANE2 #(parameter JTAG_CHAIN=1)(output reg TCK=0,CAPTURE=0,SHIFT=0,UPDATE=0,SEL=0,TDI=0,input TDO);endmodule
module qpll_common(input sys_clk,refclk,reset,output locked);
reg injected_lock=0;
assign locked=injected_lock && !reset;
endmodule
module tb;
reg sys_p=0,ref_p=0,run_ref=1;
always #2.5 sys_p=~sys_p;
always #2 if(run_ref) ref_p=~ref_p;
wire sck,mosi,cs_dac,cs_clock;
spi_probe dut(.sys_p(sys_p),.sys_n(~sys_p),.ref_p(ref_p),.ref_n(~ref_p),
 .miso(1'b0),.spi_en(1'b0),.sck(sck),.mosi(mosi),.cs_dac(cs_dac),.cs_clock(cs_clock));
task tick; begin #50;dut.probe_bs.TCK=1;#50;dut.probe_bs.TCK=0; end endtask
task capture; begin tick;tick;dut.probe_bs.SEL=1;dut.probe_bs.CAPTURE=1;tick;dut.probe_bs.CAPTURE=0; end endtask
reg [31:0] stopped;
initial begin
 #100;
 if(!dut.common.reset) $fatal(1,"reset released too early");
 #11000;
 if(dut.common.reset) $fatal(1,"startup reset stuck");
 capture;
 if(dut.scan[63:32]!==32'h41585130) $fatal(1,"unlocked signature");
 dut.common.injected_lock=1;
 capture;
 if(dut.scan[63:32]!==32'h41585131) $fatal(1,"lock synchronization");
 run_ref=0;#20;stopped=dut.count;#100;
 if(dut.count!==stopped) $fatal(1,"counter runs without reference");
 dut.common.injected_lock=0;capture;
 if(dut.scan[32]!==1'b0) $fatal(1,"lock loss hidden");
 run_ref=1;#100;
 if(dut.count==stopped) $fatal(1,"counter failed recovery");
 if(dut.gray!==(dut.count^(dut.count>>1))) $fatal(1,"Gray encoding");
 $display("SIMULATION_ONLY reset, lock status/loss, stopped reference and recovery PASS");$finish;
end
endmodule
