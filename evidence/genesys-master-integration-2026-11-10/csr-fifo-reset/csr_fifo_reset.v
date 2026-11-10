`timescale 1ns/1ps
/* Machine-generated using Migen */
module csr_fifo_reset(
	input ps_clock,
	input ps_reset,
	input tx_clock,
	input tx_reset,
	input sink_valid,
	output sink_ready,
	input [31:0] sink_data,
	output source_valid,
	input source_ready,
	output [31:0] source_data,
	output private_reset0,
	output private_reset1
);

reg sink_sink_first = 1'd0;
reg sink_sink_last = 1'd0;
wire source_source_first;
wire source_source_last;
wire cd_rst;
wire from10_clk;
wire from10_rst;
wire to10_clk;
wire to10_rst;
wire cdc_sink_valid;
wire cdc_sink_ready;
wire cdc_sink_first;
wire cdc_sink_last;
wire [31:0] cdc_sink_payload_data;
wire cdc_source_valid;
wire cdc_source_ready;
wire cdc_source_first;
wire cdc_source_last;
wire [31:0] cdc_source_payload_data;
wire cdc_asyncfifo_we;
wire cdc_asyncfifo_writable;
wire cdc_asyncfifo_re;
wire cdc_asyncfifo_readable;
wire [33:0] cdc_asyncfifo_din;
wire [33:0] cdc_asyncfifo_dout;
wire cdc_graycounter0_ce;
(* no_retiming = "true" *) reg [2:0] cdc_graycounter0_q = 3'd0;
wire [2:0] cdc_graycounter0_q_next;
reg [2:0] cdc_graycounter0_q_binary = 3'd0;
reg [2:0] cdc_graycounter0_q_next_binary;
wire cdc_graycounter1_ce;
(* no_retiming = "true" *) reg [2:0] cdc_graycounter1_q = 3'd0;
wire [2:0] cdc_graycounter1_q_next;
reg [2:0] cdc_graycounter1_q_binary = 3'd0;
reg [2:0] cdc_graycounter1_q_next_binary;
wire [2:0] cdc_produce_rdomain;
wire [2:0] cdc_consume_wdomain;
wire [1:0] cdc_wrport_adr;
wire [33:0] cdc_wrport_dat_r;
wire cdc_wrport_we;
wire [33:0] cdc_wrport_dat_w;
wire [1:0] cdc_rdport_adr;
wire [33:0] cdc_rdport_dat_r;
wire [31:0] cdc_fifo_in_payload_data;
wire cdc_fifo_in_first;
wire cdc_fifo_in_last;
wire [31:0] cdc_fifo_out_payload_data;
wire cdc_fifo_out_first;
wire cdc_fifo_out_last;
wire rst_meta0;
wire rst_meta1;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl00 = 3'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl01 = 3'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl10 = 3'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl11 = 3'd0;

// synthesis translate_off
reg dummy_s;
initial dummy_s <= 1'd0;
// synthesis translate_on

assign private_reset0 = from10_rst;
assign private_reset1 = to10_rst;
assign from10_clk = ps_clock;
assign to10_clk = tx_clock;
assign cd_rst = (ps_reset | tx_reset);
assign cdc_sink_valid = sink_valid;
assign sink_ready = cdc_sink_ready;
assign cdc_sink_first = sink_sink_first;
assign cdc_sink_last = sink_sink_last;
assign cdc_sink_payload_data = sink_data;
assign source_valid = cdc_source_valid;
assign cdc_source_ready = source_ready;
assign source_source_first = cdc_source_first;
assign source_source_last = cdc_source_last;
assign source_data = cdc_source_payload_data;
assign cdc_asyncfifo_din = {cdc_fifo_in_last, cdc_fifo_in_first, cdc_fifo_in_payload_data};
assign {cdc_fifo_out_last, cdc_fifo_out_first, cdc_fifo_out_payload_data} = cdc_asyncfifo_dout;
assign cdc_sink_ready = cdc_asyncfifo_writable;
assign cdc_asyncfifo_we = cdc_sink_valid;
assign cdc_fifo_in_first = cdc_sink_first;
assign cdc_fifo_in_last = cdc_sink_last;
assign cdc_fifo_in_payload_data = cdc_sink_payload_data;
assign cdc_source_valid = cdc_asyncfifo_readable;
assign cdc_source_first = cdc_fifo_out_first;
assign cdc_source_last = cdc_fifo_out_last;
assign cdc_source_payload_data = cdc_fifo_out_payload_data;
assign cdc_asyncfifo_re = cdc_source_ready;
assign cdc_graycounter0_ce = (cdc_asyncfifo_writable & cdc_asyncfifo_we);
assign cdc_graycounter1_ce = (cdc_asyncfifo_readable & cdc_asyncfifo_re);
assign cdc_asyncfifo_writable = (((cdc_graycounter0_q[2] == cdc_consume_wdomain[2]) | (cdc_graycounter0_q[1] == cdc_consume_wdomain[1])) | (cdc_graycounter0_q[0] != cdc_consume_wdomain[0]));
assign cdc_asyncfifo_readable = (cdc_graycounter1_q != cdc_produce_rdomain);
assign cdc_wrport_adr = cdc_graycounter0_q_binary[1:0];
assign cdc_wrport_dat_w = cdc_asyncfifo_din;
assign cdc_wrport_we = cdc_graycounter0_ce;
assign cdc_rdport_adr = cdc_graycounter1_q_next_binary[1:0];
assign cdc_asyncfifo_dout = cdc_rdport_dat_r;

// synthesis translate_off
reg dummy_d;
// synthesis translate_on
always @(*) begin
	cdc_graycounter0_q_next_binary <= 3'd0;
	if (cdc_graycounter0_ce) begin
		cdc_graycounter0_q_next_binary <= (cdc_graycounter0_q_binary + 1'd1);
	end else begin
		cdc_graycounter0_q_next_binary <= cdc_graycounter0_q_binary;
	end
// synthesis translate_off
	dummy_d <= dummy_s;
// synthesis translate_on
end
assign cdc_graycounter0_q_next = (cdc_graycounter0_q_next_binary ^ cdc_graycounter0_q_next_binary[2:1]);

// synthesis translate_off
reg dummy_d_1;
// synthesis translate_on
always @(*) begin
	cdc_graycounter1_q_next_binary <= 3'd0;
	if (cdc_graycounter1_ce) begin
		cdc_graycounter1_q_next_binary <= (cdc_graycounter1_q_binary + 1'd1);
	end else begin
		cdc_graycounter1_q_next_binary <= cdc_graycounter1_q_binary;
	end
// synthesis translate_off
	dummy_d_1 <= dummy_s;
// synthesis translate_on
end
assign cdc_graycounter1_q_next = (cdc_graycounter1_q_next_binary ^ cdc_graycounter1_q_next_binary[2:1]);
assign cdc_produce_rdomain = xilinxmultiregimpl01;
assign cdc_consume_wdomain = xilinxmultiregimpl11;

always @(posedge from10_clk) begin
	cdc_graycounter0_q_binary <= cdc_graycounter0_q_next_binary;
	cdc_graycounter0_q <= cdc_graycounter0_q_next;
	if (from10_rst) begin
		cdc_graycounter0_q <= 3'd0;
		cdc_graycounter0_q_binary <= 3'd0;
	end
	xilinxmultiregimpl10 <= cdc_graycounter1_q;
	xilinxmultiregimpl11 <= xilinxmultiregimpl10;
end

always @(posedge to10_clk) begin
	cdc_graycounter1_q_binary <= cdc_graycounter1_q_next_binary;
	cdc_graycounter1_q <= cdc_graycounter1_q_next;
	if (to10_rst) begin
		cdc_graycounter1_q <= 3'd0;
		cdc_graycounter1_q_binary <= 3'd0;
	end
	xilinxmultiregimpl00 <= cdc_graycounter0_q;
	xilinxmultiregimpl01 <= xilinxmultiregimpl00;
end

reg [33:0] storage[0:3];
reg [1:0] memadr;
reg [1:0] memadr_1;
always @(posedge from10_clk) begin : mem_write_block
	if (cdc_wrport_we)
		storage[cdc_wrport_adr] <= cdc_wrport_dat_w;
	memadr <= cdc_wrport_adr;
end

always @(posedge to10_clk) begin : mem_write_block_1
	memadr_1 <= cdc_rdport_adr;
end

assign cdc_wrport_dat_r = storage[memadr];
assign cdc_rdport_dat_r = storage[memadr_1];

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE (
	.C(from10_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(cd_rst),
	.Q(rst_meta0)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_1 (
	.C(from10_clk),
	.CE(1'd1),
	.D(rst_meta0),
	.PRE(cd_rst),
	.Q(from10_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_2 (
	.C(to10_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(cd_rst),
	.Q(rst_meta1)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_3 (
	.C(to10_clk),
	.CE(1'd1),
	.D(rst_meta1),
	.PRE(cd_rst),
	.Q(to10_rst)
);

endmodule
