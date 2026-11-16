// SPDX-License-Identifier: LGPL-3.0-or-later
`timescale 1ns/1ps
module tb_cpll_drp_sequence;
reg clk=0,testclk=0,reset=1,rdy=0;reg [15:0] dout=0;
wire [9:0] addr;wire [15:0] di;wire den,we,fail,caldone,done,userlock,progreset,progdone,pllreset,pllpd;
wire [2:0] sel;wire [17:0] count;wire [15:0] debug;
reg [15:0] memory[0:1023];integer i,delay_cycles=2,left=0,transactions=0;
reg pending=0,pwe;reg [9:0] pa;reg [15:0] pd;
time modified=0,selected=0,restored=0,completed=0;
always #4 clk=~clk;
initial begin #1;forever #4 testclk=~testclk;end
gtwizard_ultrascale_v1_7_22_gthe4_cpll_cal_tx #(.C_SIM_CPLL_CAL_BYPASS(0),.SIM_RESET_SPEEDUP("TRUE"),.C_FREERUN_FREQUENCY(125),.C_PCIE_ENABLE(0)) dut(
.TXOUTCLK_PERIOD_IN(18'd16),.CNT_TOL_IN(18'd2),.FREQ_COUNT_WINDOW_IN(16'd64),
.RESET_IN(reset),.CLK_IN(clk),.USER_TXPLLCLKSEL(2'b00),.USER_TXPROGDIVRESET_IN(1'b0),.USER_TXPRGDIVRESETDONE_OUT(progdone),
.USER_TXOUTCLKSEL_IN(3'b010),.USER_TXOUTCLK_BUFG_CE_IN(1'b1),.USER_TXOUTCLK_BUFG_CLR_IN(1'b0),.USER_CPLLLOCK_OUT(userlock),
.CPLL_CAL_FAIL(fail),.CPLL_CAL_DONE(caldone),.DEBUG_OUT(debug),.CAL_FREQ_CNT(count),.REPEAT_RESET_LIMIT(4'd0),
.GTHE4_TXOUTCLK_IN(testclk),.GTHE4_CPLLLOCK_IN(1'b1),.GTHE4_CPLLRESET_OUT(pllreset),.GTHE4_CPLLPD_OUT(pllpd),
.GTHE4_TXPROGDIVRESET_OUT(progreset),.GTHE4_TXOUTCLKSEL_OUT(sel),.GTHE4_TXPRGDIVRESETDONE_IN(1'b1),
.GTHE4_CHANNEL_DRPADDR_OUT(addr),.GTHE4_CHANNEL_DRPDI_OUT(di),.GTHE4_CHANNEL_DRPEN_OUT(den),.GTHE4_CHANNEL_DRPWE_OUT(we),
.GTHE4_CHANNEL_DRPRDY_IN(rdy),.GTHE4_CHANNEL_DRPDO_IN(dout),.DONE(done));
always @(posedge clk)begin
 rdy<=0;
 if(den&&!pending)begin pending<=1;pa<=addr;pd<=di;pwe<=we;left<=delay_cycles;end
 else if(pending)begin
  if(left>0)left<=left-1;
  else begin
   pending<=0;rdy<=1;dout<=memory[pa];transactions<=transactions+1;
   if(pwe)begin
    memory[pa]<=pd;$display("DRP_WRITE t=%0t addr=%h data=%h",$time,pa,pd);
    if(pa==10'h03e&&pd==16'he062)modified=$time;
    if(pa==10'h03e&&pd==16'he000&&modified!=0)restored=$time;
   end
  end
 end
end
always @(sel)if(sel==3'b101&&selected==0)selected=$time;
always @(posedge caldone)completed=$time;
task check;input ok;input [511:0] label;begin if(ok!==1'b1)$fatal(1,"FAIL %s",label);end endtask
initial begin
 if($value$plusargs("DRP_DELAY=%d",delay_cycles))begin end
 for(i=0;i<1024;i=i+1)memory[i]=0;
 memory[10'h03e]=16'he000; // Explicit emulated original word, not a hardware backup.
 #200;reset=0;
 wait(caldone||fail);#100;
 check(caldone&&!fail,"non-bypassed calibration completes");
 check(modified>0&&selected>modified&&restored>selected&&completed>restored,"modify/select/restore/done order");
 check(memory[10'h03e]==16'he000,"original modeled divider restored");
 check(sel==3'b010&&userlock&&done,"user selector and lock restored after completion");
 $display("CPLL_DRP_SEQUENCE_PASS delay=%0d transactions=%0d measured=%0d modify=%0t select=%0t restore=%0t done=%0t",delay_cycles,transactions,count,modified,selected,restored,completed);
 $finish;
end
initial begin #1000000;$fatal(1,"timeout");end
endmodule
