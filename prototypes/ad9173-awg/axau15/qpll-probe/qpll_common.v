/* Machine-generated using Migen */
module qpll_common(
	input sys_clk,
	input refclk,
	input reset,
	output locked
);

wire gth4quadpll_clk;
wire gth4quadpll_refclk;
wire gth4quadpll_reset;
wire gth4quadpll_lock;
wire gth4quadpll_powerdown;
wire gth4quadpll_drp_clk;
wire gth4quadpll_drp_en;
wire gth4quadpll_drp_we;
wire gth4quadpll_drp_rdy;
wire [8:0] gth4quadpll_drp_addr;
wire [15:0] gth4quadpll_drp_di;
wire [15:0] gth4quadpll_drp_do;
wire gth4quadpll0;
wire gth4quadpll1;
wire gth4quadpll2;

// synthesis translate_off
reg dummy_s;
initial dummy_s <= 1'd0;
// synthesis translate_on

assign gth4quadpll_reset = reset;
assign gth4quadpll_powerdown = 1'd0;
assign locked = gth4quadpll_lock;
assign gth4quadpll_drp_clk = sys_clk;
assign gth4quadpll_drp_addr = 1'd0;
assign gth4quadpll_drp_di = 1'd0;
assign gth4quadpll_drp_en = 1'd0;
assign gth4quadpll_drp_we = 1'd0;

GTHE4_COMMON #(
	.BIAS_CFG0(1'd0),
	.BIAS_CFG1(1'd0),
	.BIAS_CFG2(9'd292),
	.BIAS_CFG3(7'd65),
	.BIAS_CFG4(5'd16),
	.BIAS_CFG_RSVD(1'd0),
	.PPF0_CFG(11'd1536),
	.PPF1_CFG(11'd1536),
	.QPLL0CLKOUT_RATE("HALF"),
	.QPLL0_CFG0(14'd13084),
	.QPLL0_CFG1(16'd53304),
	.QPLL0_CFG1_G3(16'd53304),
	.QPLL0_CFG2(16'd34752),
	.QPLL0_CFG2_G3(16'd34752),
	.QPLL0_CFG3(9'd288),
	.QPLL0_CFG4(2'd3),
	.QPLL0_CP(8'd255),
	.QPLL0_CP_G3(4'd15),
	.QPLL0_FBDIV(7'd100),
	.QPLL0_FBDIV_G3(7'd100),
	.QPLL0_INIT_CFG0(10'd690),
	.QPLL0_INIT_CFG1(1'd0),
	.QPLL0_LOCK_CFG(14'd9704),
	.QPLL0_LOCK_CFG_G3(14'd9704),
	.QPLL0_LPF(10'd543),
	.QPLL0_LPF_G3(9'd469),
	.QPLL0_RATE_SW_USE_DRP(1'd1),
	.QPLL0_REFCLK_DIV(2'd2),
	.QPLL1CLKOUT_RATE("HALF"),
	.QPLL1_CFG0(14'd13084),
	.QPLL1_CFG1(16'd53304),
	.QPLL1_CFG1_G3(16'd53304),
	.QPLL1_CFG2(12'd4035),
	.QPLL1_CFG2_G3(12'd4035),
	.QPLL1_CFG3(9'd288),
	.QPLL1_CFG4(2'd3),
	.QPLL1_CP(8'd255),
	.QPLL1_CP_G3(7'd127),
	.QPLL1_FBDIV(7'd100),
	.QPLL1_FBDIV_G3(7'd100),
	.QPLL1_INIT_CFG0(10'd690),
	.QPLL1_INIT_CFG1(1'd0),
	.QPLL1_LOCK_CFG(14'd9704),
	.QPLL1_LOCK_CFG_G3(14'd9704),
	.QPLL1_LPF(10'd543),
	.QPLL1_LPF_G3(9'd468),
	.QPLL1_RATE_SW_USE_DRP(1'd1),
	.QPLL1_REFCLK_DIV(2'd2)
) GTHE4_COMMON (
	.BGBYPASSB(1'd1),
	.BGMONITORENB(1'd1),
	.BGPDB(1'd1),
	.BGRCALOVRD(5'd31),
	.BGRCALOVRDENB(1'd1),
	.DRPADDR(gth4quadpll_drp_addr),
	.DRPCLK(gth4quadpll_drp_clk),
	.DRPDI(gth4quadpll_drp_di),
	.DRPEN(gth4quadpll_drp_en),
	.DRPWE(gth4quadpll_drp_we),
	.GTGREFCLK0(1'd0),
	.GTGREFCLK1(1'd0),
	.GTREFCLK00(refclk),
	.GTREFCLK01(refclk),
	.QPLL0CLKRSVD0(1'd0),
	.QPLL0CLKRSVD1(1'd0),
	.QPLL0FBDIV(1'd0),
	.QPLL0LOCKDETCLK(sys_clk),
	.QPLL0LOCKEN(1'd1),
	.QPLL0PD(1'd1),
	.QPLL0REFCLKSEL(1'd1),
	.QPLL0RESET(gth4quadpll_reset),
	.QPLL1CLKRSVD0(1'd0),
	.QPLL1CLKRSVD1(1'd0),
	.QPLL1FBDIV(1'd0),
	.QPLL1LOCKDETCLK(sys_clk),
	.QPLL1LOCKEN(1'd1),
	.QPLL1PD(gth4quadpll_powerdown),
	.QPLL1REFCLKSEL(1'd1),
	.QPLL1RESET(gth4quadpll_reset),
	.QPLLRSVD1(1'd0),
	.QPLLRSVD2(1'd0),
	.QPLLRSVD3(1'd0),
	.QPLLRSVD4(1'd0),
	.RCALENB(1'd1),
	.SDM0DATA(1'd0),
	.SDM0RESET(1'd0),
	.SDM0WIDTH(1'd0),
	.SDM1DATA(1'd0),
	.SDM1RESET(1'd0),
	.SDM1WIDTH(1'd0),
	.DRPDO(gth4quadpll_drp_do),
	.DRPRDY(gth4quadpll_drp_rdy),
	.QPLL0LOCK(gth4quadpll0),
	.QPLL0OUTCLK(gth4quadpll1),
	.QPLL0OUTREFCLK(gth4quadpll2),
	.QPLL1LOCK(gth4quadpll_lock),
	.QPLL1OUTCLK(gth4quadpll_clk),
	.QPLL1OUTREFCLK(gth4quadpll_refclk)
);

endmodule
