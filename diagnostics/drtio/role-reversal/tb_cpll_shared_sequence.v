// SPDX-License-Identifier: LGPL-3.0-or-later
`timescale 1ns/1ps
module tb_cpll_shared_sequence;
reg clk=0,testclk=0,reset=1,rdy=0;reg [15:0] dout=0;
wire [9:0] addr;wire [15:0] di;wire den,we,fail,caldone,done,userlock,progreset,progdone,pllreset,pllpd;
wire [2:0] sel;wire [17:0] count;wire [15:0] debug;
reg [15:0] memory[0:1023];integer i,delay_cycles=2,left=0,transactions=0;
integer mode=0;reg gtlock=1,gtprogdone=1;
reg pending=0,pwe;reg [9:0] pa;reg [15:0] pd;
time modified=0,selected=0,restored=0,completed=0;
reg txactive=0;
wire helper_done,helper_reset,helper_ready,helper_pllreset,rx_pllreset,rx_done;
// Shared CPLL reset feedback from enabled TX and RX; GT status remains modeled.
gtwizard_ultrascale_v1_7_22_gtwiz_reset #(.P_FREERUN_FREQUENCY(125),.P_USE_CPLL_CAL(0),.P_TX_PLL_TYPE(2),.P_RX_PLL_TYPE(2),.P_RX_LINE_RATE(2.5)) helper(
.gtwiz_reset_clk_freerun_in(clk),.gtwiz_reset_all_in(reset),
.gtwiz_reset_tx_pll_and_datapath_in(1'b0),.gtwiz_reset_tx_datapath_in(1'b0),
.gtwiz_reset_rx_pll_and_datapath_in(1'b0),.gtwiz_reset_rx_datapath_in(1'b0),
.gtwiz_reset_userclk_tx_active_in(txactive),.gtwiz_reset_userclk_rx_active_in(txactive),
.gtpowergood_in(1'b1),.txusrclk2_in(testclk),.rxusrclk2_in(testclk),
.plllock_tx_in(userlock),.plllock_rx_in(userlock),.txresetdone_in(1'b1),
.rxcdrlock_in(1'b1),.rxresetdone_in(1'b1),.tx_enabled_tie_in(1'b1),.rx_enabled_tie_in(1'b1),.shared_pll_tie_in(1'b1),
.pllreset_rx_out(rx_pllreset),.gtwiz_reset_rx_done_out(rx_done),.pllreset_tx_out(helper_pllreset),.gtwiz_reset_tx_done_out(helper_done),.gttxreset_out(helper_reset),.txuserrdy_out(helper_ready));
always #4 clk=~clk;
initial begin #1;forever #4 testclk=~testclk;end
gtwizard_ultrascale_v1_7_22_gthe4_cpll_cal #(.C_TX_PLL_TYPE(2),.C_RX_PLL_TYPE(2),.C_SIM_CPLL_CAL_BYPASS(0),.SIM_RESET_SPEEDUP("TRUE"),.C_FREERUN_FREQUENCY(125),.C_PCIE_ENABLE(0)) dut(
.TXOUTCLK_PERIOD_IN(18'd16),.CNT_TOL_IN(18'd2),.FREQ_COUNT_WINDOW_IN(16'd64),
.RESET_IN(reset|helper_pllreset|rx_pllreset),.CLK_IN(clk),.USER_TXPLLCLKSEL(2'b00),.USER_TXPROGDIVRESET_IN(1'b0),.USER_TXPRGDIVRESETDONE_OUT(progdone),
.USER_TXOUTCLKSEL_IN(3'b010),.USER_TXOUTCLK_BUFG_CE_IN(1'b1),.USER_TXOUTCLK_BUFG_CLR_IN(1'b0),.USER_CPLLLOCK_OUT(userlock),
.CPLL_CAL_FAIL(fail),.CPLL_CAL_DONE(caldone),.DEBUG_OUT(debug),.CAL_FREQ_CNT(count),.REPEAT_RESET_LIMIT(4'd0),
.GTHE4_TXOUTCLK_IN(testclk),.GTHE4_CPLLLOCK_IN(gtlock),.GTHE4_CPLLRESET_OUT(pllreset),.GTHE4_CPLLPD_OUT(pllpd),
.GTHE4_TXPROGDIVRESET_OUT(progreset),.GTHE4_TXOUTCLKSEL_OUT(sel),.GTHE4_TXPRGDIVRESETDONE_IN(gtprogdone),
.GTHE4_CHANNEL_DRPADDR_OUT(addr),.GTHE4_CHANNEL_DRPDI_OUT(di),.GTHE4_CHANNEL_DRPEN_OUT(den),.GTHE4_CHANNEL_DRPWE_OUT(we),
.GTHE4_CHANNEL_DRPRDY_IN(rdy),.GTHE4_CHANNEL_DRPDO_IN(dout),.DRPRST_IN(reset),.USER_RXPLLCLKSEL(2'b00),.USER_RXPROGDIVRESET_IN(1'b0),
.USER_RXOUTCLKSEL_IN(3'b010),.USER_RXOUTCLK_BUFG_CE_IN(1'b1),.USER_RXOUTCLK_BUFG_CLR_IN(1'b0),
.USER_GTRXRESET_IN(1'b0),.USER_RXCDRHOLD_IN(1'b0),.USER_RXPMARESET_IN(1'b0),
.USER_CHANNEL_DRPADDR_IN(10'b0),.USER_CHANNEL_DRPDI_IN(16'b0),.USER_CHANNEL_DRPEN_IN(1'b0),.USER_CHANNEL_DRPWE_IN(1'b0),
.GTHE4_RXOUTCLK_IN(testclk),.GTHE4_RXPRGDIVRESETDONE_IN(1'b1),.GTHE4_RXPMARESETDONE_IN(1'b1));
// Same generated TX/RX PLL type forces TX calibration; inactive RX must not leak lock.
always @(negedge clk)if(!reset)begin
 check(dut.cpll_cal_on_tx_or_rx===1'b0,"actual equal PLL types select TX");
 check(dut.cal_on_rx_cplllock_out===1'b0,"inactive RX lock masked");
end
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
 if($value$plusargs("MODE=%d",mode))begin end
 check(mode>=0&&mode<=2,"supported mode");
 if(mode==1)gtprogdone=0;
 if(mode==2)gtlock=0;
 for(i=0;i<1024;i=i+1)memory[i]=0;
 memory[10'h03e]=16'he000; // Explicit emulated original word, not a hardware backup.
 #200;reset=0;
 if(mode==1)begin
  @(posedge progreset);@(negedge progreset);#200;
  check(!caldone&&!fail&&!userlock,"withheld divider done blocks completion and user lock");
  $display("WITHHELD_PROGDIV_PASS t=%0t",$time);
  gtprogdone=1;
 end
 wait(caldone||fail);#100;
 if(mode==2)begin
  check(!helper_done&&helper_reset,"missing lock holds helper reset");
  check(fail&&!caldone&&!userlock,"missing raw lock fails calibration and masks user lock");
  check(restored>selected&&memory[10'h03e]==16'he000,"failure restores divider");
  $display("CPLL_SHARED_SEQUENCE_PASS mode=2 missing_lock_failure transactions=%0d",transactions);
  $finish;
 end
 check(caldone&&!fail,"non-bypassed calibration completes");
 check(modified>0&&selected>modified&&restored>selected&&completed>restored,"modify/select/restore/done order");
 check(memory[10'h03e]==16'he000,"original modeled divider restored");
 check(sel==3'b010&&userlock ,"user selector and lock restored after completion");
 wait(!helper_reset);#100;
 check(!helper_ready&&!helper_done,"inactive user clock blocks ready and completion");
 txactive=1;wait(helper_done&&rx_done);#100;
 check(!helper_pllreset&&!rx_pllreset,"both shared PLL reset requests released");
 check(helper_ready&&!helper_reset,"helper completes with clock active and lock");
 gtlock=0;repeat(40)@(posedge clk);#1;
 check(!helper_done,"helper withdraws done after lock loss");
 check(!helper_reset,"IDLE lock loss does not restart datapath reset");
 check(!userlock,"raw lock withdrawal propagates after success");
 $display("CPLL_SHARED_SEQUENCE_PASS delay=%0d transactions=%0d measured=%0d modify=%0t select=%0t restore=%0t done=%0t",delay_cycles,transactions,count,modified,selected,restored,completed);
 $finish;
end
initial begin #1000000;$fatal(1,"timeout");end
endmodule
