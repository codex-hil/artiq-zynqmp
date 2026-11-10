`timescale 1ns/1ps
/* Machine-generated using Migen */
module ps_cdc_reset(
	input ps_clock,
	input ps_reset,
	input tx_clock,
	input tx_reset,
	input aw_sink_valid,
	output aw_sink_ready,
	input w_sink_valid,
	output w_sink_ready,
	output b_source_valid,
	input b_source_ready,
	input ar_sink_valid,
	output ar_sink_ready,
	output r_source_valid,
	input r_source_ready,
	output aw_source_valid,
	input aw_source_ready,
	output w_source_valid,
	input w_source_ready,
	input b_sink_valid,
	output b_sink_ready,
	output ar_source_valid,
	input ar_source_ready,
	input r_sink_valid,
	output r_sink_ready,
	input [44:0] aw_input,
	output [44:0] aw_output,
	input [37:0] w_input,
	output [37:0] w_output,
	input [3:0] b_input,
	output [3:0] b_output,
	input [44:0] ar_input,
	output [44:0] ar_output,
	input [35:0] r_input,
	output [35:0] r_output,
	output reg [9:0] private_resets
);

wire ps_aw_first;
wire ps_aw_last;
wire [39:0] ps_aw_payload_addr;
wire [2:0] ps_aw_payload_prot;
wire ps_w_first;
wire ps_w_last;
wire [31:0] ps_w_payload_data;
wire [3:0] ps_w_payload_strb;
wire ps_b_first;
wire ps_b_last;
wire [1:0] ps_b_payload_resp;
wire ps_ar_first;
wire ps_ar_last;
wire [39:0] ps_ar_payload_addr;
wire [2:0] ps_ar_payload_prot;
wire ps_r_first;
wire ps_r_last;
wire [1:0] ps_r_payload_resp;
wire [31:0] ps_r_payload_data;
wire tx_aw_first;
wire tx_aw_last;
wire [39:0] tx_aw_payload_addr;
wire [2:0] tx_aw_payload_prot;
wire tx_w_first;
wire tx_w_last;
wire [31:0] tx_w_payload_data;
wire [3:0] tx_w_payload_strb;
wire tx_b_first;
wire tx_b_last;
wire [1:0] tx_b_payload_resp;
wire tx_ar_first;
wire tx_ar_last;
wire [39:0] tx_ar_payload_addr;
wire [2:0] tx_ar_payload_prot;
wire tx_r_first;
wire tx_r_last;
wire [1:0] tx_r_payload_resp;
wire [31:0] tx_r_payload_data;
wire clockdomaincrossing0_sink_sink_valid;
wire clockdomaincrossing0_sink_sink_ready;
wire clockdomaincrossing0_sink_sink_first;
wire clockdomaincrossing0_sink_sink_last;
wire [39:0] clockdomaincrossing0_sink_sink_payload_addr;
wire [2:0] clockdomaincrossing0_sink_sink_payload_prot;
wire clockdomaincrossing0_source_source_valid;
wire clockdomaincrossing0_source_source_ready;
wire clockdomaincrossing0_source_source_first;
wire clockdomaincrossing0_source_source_last;
wire [39:0] clockdomaincrossing0_source_source_payload_addr;
wire [2:0] clockdomaincrossing0_source_source_payload_prot;
wire clockdomaincrossing0_cd_rst;
wire from126_clk;
wire from126_rst;
wire to126_clk;
wire to126_rst;
wire clockdomaincrossing0_cdc_sink_valid;
wire clockdomaincrossing0_cdc_sink_ready;
wire clockdomaincrossing0_cdc_sink_first;
wire clockdomaincrossing0_cdc_sink_last;
wire [39:0] clockdomaincrossing0_cdc_sink_payload_addr;
wire [2:0] clockdomaincrossing0_cdc_sink_payload_prot;
wire clockdomaincrossing0_cdc_source_valid;
wire clockdomaincrossing0_cdc_source_ready;
wire clockdomaincrossing0_cdc_source_first;
wire clockdomaincrossing0_cdc_source_last;
wire [39:0] clockdomaincrossing0_cdc_source_payload_addr;
wire [2:0] clockdomaincrossing0_cdc_source_payload_prot;
wire clockdomaincrossing0_cdc_asyncfifo0_we;
wire clockdomaincrossing0_cdc_asyncfifo0_writable;
wire clockdomaincrossing0_cdc_asyncfifo0_re;
wire clockdomaincrossing0_cdc_asyncfifo0_readable;
wire [44:0] clockdomaincrossing0_cdc_asyncfifo0_din;
wire [44:0] clockdomaincrossing0_cdc_asyncfifo0_dout;
wire clockdomaincrossing0_cdc_graycounter0_ce;
(* no_retiming = "true" *) reg [2:0] clockdomaincrossing0_cdc_graycounter0_q = 3'd0;
wire [2:0] clockdomaincrossing0_cdc_graycounter0_q_next;
reg [2:0] clockdomaincrossing0_cdc_graycounter0_q_binary = 3'd0;
reg [2:0] clockdomaincrossing0_cdc_graycounter0_q_next_binary;
wire clockdomaincrossing0_cdc_graycounter1_ce;
(* no_retiming = "true" *) reg [2:0] clockdomaincrossing0_cdc_graycounter1_q = 3'd0;
wire [2:0] clockdomaincrossing0_cdc_graycounter1_q_next;
reg [2:0] clockdomaincrossing0_cdc_graycounter1_q_binary = 3'd0;
reg [2:0] clockdomaincrossing0_cdc_graycounter1_q_next_binary;
wire [2:0] clockdomaincrossing0_cdc_produce_rdomain;
wire [2:0] clockdomaincrossing0_cdc_consume_wdomain;
wire [1:0] clockdomaincrossing0_cdc_wrport_adr;
wire [44:0] clockdomaincrossing0_cdc_wrport_dat_r;
wire clockdomaincrossing0_cdc_wrport_we;
wire [44:0] clockdomaincrossing0_cdc_wrport_dat_w;
wire [1:0] clockdomaincrossing0_cdc_rdport_adr;
wire [44:0] clockdomaincrossing0_cdc_rdport_dat_r;
wire [39:0] clockdomaincrossing0_cdc_fifo_in_payload_addr;
wire [2:0] clockdomaincrossing0_cdc_fifo_in_payload_prot;
wire clockdomaincrossing0_cdc_fifo_in_first;
wire clockdomaincrossing0_cdc_fifo_in_last;
wire [39:0] clockdomaincrossing0_cdc_fifo_out_payload_addr;
wire [2:0] clockdomaincrossing0_cdc_fifo_out_payload_prot;
wire clockdomaincrossing0_cdc_fifo_out_first;
wire clockdomaincrossing0_cdc_fifo_out_last;
wire clockdomaincrossing1_sink_sink_valid;
wire clockdomaincrossing1_sink_sink_ready;
wire clockdomaincrossing1_sink_sink_first;
wire clockdomaincrossing1_sink_sink_last;
wire [31:0] clockdomaincrossing1_sink_sink_payload_data;
wire [3:0] clockdomaincrossing1_sink_sink_payload_strb;
wire clockdomaincrossing1_source_source_valid;
wire clockdomaincrossing1_source_source_ready;
wire clockdomaincrossing1_source_source_first;
wire clockdomaincrossing1_source_source_last;
wire [31:0] clockdomaincrossing1_source_source_payload_data;
wire [3:0] clockdomaincrossing1_source_source_payload_strb;
wire clockdomaincrossing1_cd_rst;
wire from289_clk;
wire from289_rst;
wire to289_clk;
wire to289_rst;
wire clockdomaincrossing1_cdc_sink_valid;
wire clockdomaincrossing1_cdc_sink_ready;
wire clockdomaincrossing1_cdc_sink_first;
wire clockdomaincrossing1_cdc_sink_last;
wire [31:0] clockdomaincrossing1_cdc_sink_payload_data;
wire [3:0] clockdomaincrossing1_cdc_sink_payload_strb;
wire clockdomaincrossing1_cdc_source_valid;
wire clockdomaincrossing1_cdc_source_ready;
wire clockdomaincrossing1_cdc_source_first;
wire clockdomaincrossing1_cdc_source_last;
wire [31:0] clockdomaincrossing1_cdc_source_payload_data;
wire [3:0] clockdomaincrossing1_cdc_source_payload_strb;
wire clockdomaincrossing1_cdc_asyncfifo1_we;
wire clockdomaincrossing1_cdc_asyncfifo1_writable;
wire clockdomaincrossing1_cdc_asyncfifo1_re;
wire clockdomaincrossing1_cdc_asyncfifo1_readable;
wire [37:0] clockdomaincrossing1_cdc_asyncfifo1_din;
wire [37:0] clockdomaincrossing1_cdc_asyncfifo1_dout;
wire clockdomaincrossing1_cdc_graycounter2_ce;
(* no_retiming = "true" *) reg [2:0] clockdomaincrossing1_cdc_graycounter2_q = 3'd0;
wire [2:0] clockdomaincrossing1_cdc_graycounter2_q_next;
reg [2:0] clockdomaincrossing1_cdc_graycounter2_q_binary = 3'd0;
reg [2:0] clockdomaincrossing1_cdc_graycounter2_q_next_binary;
wire clockdomaincrossing1_cdc_graycounter3_ce;
(* no_retiming = "true" *) reg [2:0] clockdomaincrossing1_cdc_graycounter3_q = 3'd0;
wire [2:0] clockdomaincrossing1_cdc_graycounter3_q_next;
reg [2:0] clockdomaincrossing1_cdc_graycounter3_q_binary = 3'd0;
reg [2:0] clockdomaincrossing1_cdc_graycounter3_q_next_binary;
wire [2:0] clockdomaincrossing1_cdc_produce_rdomain;
wire [2:0] clockdomaincrossing1_cdc_consume_wdomain;
wire [1:0] clockdomaincrossing1_cdc_wrport_adr;
wire [37:0] clockdomaincrossing1_cdc_wrport_dat_r;
wire clockdomaincrossing1_cdc_wrport_we;
wire [37:0] clockdomaincrossing1_cdc_wrport_dat_w;
wire [1:0] clockdomaincrossing1_cdc_rdport_adr;
wire [37:0] clockdomaincrossing1_cdc_rdport_dat_r;
wire [31:0] clockdomaincrossing1_cdc_fifo_in_payload_data;
wire [3:0] clockdomaincrossing1_cdc_fifo_in_payload_strb;
wire clockdomaincrossing1_cdc_fifo_in_first;
wire clockdomaincrossing1_cdc_fifo_in_last;
wire [31:0] clockdomaincrossing1_cdc_fifo_out_payload_data;
wire [3:0] clockdomaincrossing1_cdc_fifo_out_payload_strb;
wire clockdomaincrossing1_cdc_fifo_out_first;
wire clockdomaincrossing1_cdc_fifo_out_last;
wire clockdomaincrossing2_sink_sink_valid;
wire clockdomaincrossing2_sink_sink_ready;
wire clockdomaincrossing2_sink_sink_first;
wire clockdomaincrossing2_sink_sink_last;
wire [1:0] clockdomaincrossing2_sink_sink_payload_resp;
wire clockdomaincrossing2_source_source_valid;
wire clockdomaincrossing2_source_source_ready;
wire clockdomaincrossing2_source_source_first;
wire clockdomaincrossing2_source_source_last;
wire [1:0] clockdomaincrossing2_source_source_payload_resp;
wire clockdomaincrossing2_cd_rst;
wire from452_clk;
wire from452_rst;
wire to452_clk;
wire to452_rst;
wire clockdomaincrossing2_cdc_sink_valid;
wire clockdomaincrossing2_cdc_sink_ready;
wire clockdomaincrossing2_cdc_sink_first;
wire clockdomaincrossing2_cdc_sink_last;
wire [1:0] clockdomaincrossing2_cdc_sink_payload_resp;
wire clockdomaincrossing2_cdc_source_valid;
wire clockdomaincrossing2_cdc_source_ready;
wire clockdomaincrossing2_cdc_source_first;
wire clockdomaincrossing2_cdc_source_last;
wire [1:0] clockdomaincrossing2_cdc_source_payload_resp;
wire clockdomaincrossing2_cdc_asyncfifo2_we;
wire clockdomaincrossing2_cdc_asyncfifo2_writable;
wire clockdomaincrossing2_cdc_asyncfifo2_re;
wire clockdomaincrossing2_cdc_asyncfifo2_readable;
wire [3:0] clockdomaincrossing2_cdc_asyncfifo2_din;
wire [3:0] clockdomaincrossing2_cdc_asyncfifo2_dout;
wire clockdomaincrossing2_cdc_graycounter4_ce;
(* no_retiming = "true" *) reg [2:0] clockdomaincrossing2_cdc_graycounter4_q = 3'd0;
wire [2:0] clockdomaincrossing2_cdc_graycounter4_q_next;
reg [2:0] clockdomaincrossing2_cdc_graycounter4_q_binary = 3'd0;
reg [2:0] clockdomaincrossing2_cdc_graycounter4_q_next_binary;
wire clockdomaincrossing2_cdc_graycounter5_ce;
(* no_retiming = "true" *) reg [2:0] clockdomaincrossing2_cdc_graycounter5_q = 3'd0;
wire [2:0] clockdomaincrossing2_cdc_graycounter5_q_next;
reg [2:0] clockdomaincrossing2_cdc_graycounter5_q_binary = 3'd0;
reg [2:0] clockdomaincrossing2_cdc_graycounter5_q_next_binary;
wire [2:0] clockdomaincrossing2_cdc_produce_rdomain;
wire [2:0] clockdomaincrossing2_cdc_consume_wdomain;
wire [1:0] clockdomaincrossing2_cdc_wrport_adr;
wire [3:0] clockdomaincrossing2_cdc_wrport_dat_r;
wire clockdomaincrossing2_cdc_wrport_we;
wire [3:0] clockdomaincrossing2_cdc_wrport_dat_w;
wire [1:0] clockdomaincrossing2_cdc_rdport_adr;
wire [3:0] clockdomaincrossing2_cdc_rdport_dat_r;
wire [1:0] clockdomaincrossing2_cdc_fifo_in_payload_resp;
wire clockdomaincrossing2_cdc_fifo_in_first;
wire clockdomaincrossing2_cdc_fifo_in_last;
wire [1:0] clockdomaincrossing2_cdc_fifo_out_payload_resp;
wire clockdomaincrossing2_cdc_fifo_out_first;
wire clockdomaincrossing2_cdc_fifo_out_last;
wire clockdomaincrossing3_sink_sink_valid;
wire clockdomaincrossing3_sink_sink_ready;
wire clockdomaincrossing3_sink_sink_first;
wire clockdomaincrossing3_sink_sink_last;
wire [39:0] clockdomaincrossing3_sink_sink_payload_addr;
wire [2:0] clockdomaincrossing3_sink_sink_payload_prot;
wire clockdomaincrossing3_source_source_valid;
wire clockdomaincrossing3_source_source_ready;
wire clockdomaincrossing3_source_source_first;
wire clockdomaincrossing3_source_source_last;
wire [39:0] clockdomaincrossing3_source_source_payload_addr;
wire [2:0] clockdomaincrossing3_source_source_payload_prot;
wire clockdomaincrossing3_cd_rst;
wire from603_clk;
wire from603_rst;
wire to603_clk;
wire to603_rst;
wire clockdomaincrossing3_cdc_sink_valid;
wire clockdomaincrossing3_cdc_sink_ready;
wire clockdomaincrossing3_cdc_sink_first;
wire clockdomaincrossing3_cdc_sink_last;
wire [39:0] clockdomaincrossing3_cdc_sink_payload_addr;
wire [2:0] clockdomaincrossing3_cdc_sink_payload_prot;
wire clockdomaincrossing3_cdc_source_valid;
wire clockdomaincrossing3_cdc_source_ready;
wire clockdomaincrossing3_cdc_source_first;
wire clockdomaincrossing3_cdc_source_last;
wire [39:0] clockdomaincrossing3_cdc_source_payload_addr;
wire [2:0] clockdomaincrossing3_cdc_source_payload_prot;
wire clockdomaincrossing3_cdc_asyncfifo3_we;
wire clockdomaincrossing3_cdc_asyncfifo3_writable;
wire clockdomaincrossing3_cdc_asyncfifo3_re;
wire clockdomaincrossing3_cdc_asyncfifo3_readable;
wire [44:0] clockdomaincrossing3_cdc_asyncfifo3_din;
wire [44:0] clockdomaincrossing3_cdc_asyncfifo3_dout;
wire clockdomaincrossing3_cdc_graycounter6_ce;
(* no_retiming = "true" *) reg [2:0] clockdomaincrossing3_cdc_graycounter6_q = 3'd0;
wire [2:0] clockdomaincrossing3_cdc_graycounter6_q_next;
reg [2:0] clockdomaincrossing3_cdc_graycounter6_q_binary = 3'd0;
reg [2:0] clockdomaincrossing3_cdc_graycounter6_q_next_binary;
wire clockdomaincrossing3_cdc_graycounter7_ce;
(* no_retiming = "true" *) reg [2:0] clockdomaincrossing3_cdc_graycounter7_q = 3'd0;
wire [2:0] clockdomaincrossing3_cdc_graycounter7_q_next;
reg [2:0] clockdomaincrossing3_cdc_graycounter7_q_binary = 3'd0;
reg [2:0] clockdomaincrossing3_cdc_graycounter7_q_next_binary;
wire [2:0] clockdomaincrossing3_cdc_produce_rdomain;
wire [2:0] clockdomaincrossing3_cdc_consume_wdomain;
wire [1:0] clockdomaincrossing3_cdc_wrport_adr;
wire [44:0] clockdomaincrossing3_cdc_wrport_dat_r;
wire clockdomaincrossing3_cdc_wrport_we;
wire [44:0] clockdomaincrossing3_cdc_wrport_dat_w;
wire [1:0] clockdomaincrossing3_cdc_rdport_adr;
wire [44:0] clockdomaincrossing3_cdc_rdport_dat_r;
wire [39:0] clockdomaincrossing3_cdc_fifo_in_payload_addr;
wire [2:0] clockdomaincrossing3_cdc_fifo_in_payload_prot;
wire clockdomaincrossing3_cdc_fifo_in_first;
wire clockdomaincrossing3_cdc_fifo_in_last;
wire [39:0] clockdomaincrossing3_cdc_fifo_out_payload_addr;
wire [2:0] clockdomaincrossing3_cdc_fifo_out_payload_prot;
wire clockdomaincrossing3_cdc_fifo_out_first;
wire clockdomaincrossing3_cdc_fifo_out_last;
wire clockdomaincrossing4_sink_sink_valid;
wire clockdomaincrossing4_sink_sink_ready;
wire clockdomaincrossing4_sink_sink_first;
wire clockdomaincrossing4_sink_sink_last;
wire [1:0] clockdomaincrossing4_sink_sink_payload_resp;
wire [31:0] clockdomaincrossing4_sink_sink_payload_data;
wire clockdomaincrossing4_source_source_valid;
wire clockdomaincrossing4_source_source_ready;
wire clockdomaincrossing4_source_source_first;
wire clockdomaincrossing4_source_source_last;
wire [1:0] clockdomaincrossing4_source_source_payload_resp;
wire [31:0] clockdomaincrossing4_source_source_payload_data;
wire clockdomaincrossing4_cd_rst;
wire from766_clk;
wire from766_rst;
wire to766_clk;
wire to766_rst;
wire clockdomaincrossing4_cdc_sink_valid;
wire clockdomaincrossing4_cdc_sink_ready;
wire clockdomaincrossing4_cdc_sink_first;
wire clockdomaincrossing4_cdc_sink_last;
wire [1:0] clockdomaincrossing4_cdc_sink_payload_resp;
wire [31:0] clockdomaincrossing4_cdc_sink_payload_data;
wire clockdomaincrossing4_cdc_source_valid;
wire clockdomaincrossing4_cdc_source_ready;
wire clockdomaincrossing4_cdc_source_first;
wire clockdomaincrossing4_cdc_source_last;
wire [1:0] clockdomaincrossing4_cdc_source_payload_resp;
wire [31:0] clockdomaincrossing4_cdc_source_payload_data;
wire clockdomaincrossing4_cdc_asyncfifo4_we;
wire clockdomaincrossing4_cdc_asyncfifo4_writable;
wire clockdomaincrossing4_cdc_asyncfifo4_re;
wire clockdomaincrossing4_cdc_asyncfifo4_readable;
wire [35:0] clockdomaincrossing4_cdc_asyncfifo4_din;
wire [35:0] clockdomaincrossing4_cdc_asyncfifo4_dout;
wire clockdomaincrossing4_cdc_graycounter8_ce;
(* no_retiming = "true" *) reg [2:0] clockdomaincrossing4_cdc_graycounter8_q = 3'd0;
wire [2:0] clockdomaincrossing4_cdc_graycounter8_q_next;
reg [2:0] clockdomaincrossing4_cdc_graycounter8_q_binary = 3'd0;
reg [2:0] clockdomaincrossing4_cdc_graycounter8_q_next_binary;
wire clockdomaincrossing4_cdc_graycounter9_ce;
(* no_retiming = "true" *) reg [2:0] clockdomaincrossing4_cdc_graycounter9_q = 3'd0;
wire [2:0] clockdomaincrossing4_cdc_graycounter9_q_next;
reg [2:0] clockdomaincrossing4_cdc_graycounter9_q_binary = 3'd0;
reg [2:0] clockdomaincrossing4_cdc_graycounter9_q_next_binary;
wire [2:0] clockdomaincrossing4_cdc_produce_rdomain;
wire [2:0] clockdomaincrossing4_cdc_consume_wdomain;
wire [1:0] clockdomaincrossing4_cdc_wrport_adr;
wire [35:0] clockdomaincrossing4_cdc_wrport_dat_r;
wire clockdomaincrossing4_cdc_wrport_we;
wire [35:0] clockdomaincrossing4_cdc_wrport_dat_w;
wire [1:0] clockdomaincrossing4_cdc_rdport_adr;
wire [35:0] clockdomaincrossing4_cdc_rdport_dat_r;
wire [1:0] clockdomaincrossing4_cdc_fifo_in_payload_resp;
wire [31:0] clockdomaincrossing4_cdc_fifo_in_payload_data;
wire clockdomaincrossing4_cdc_fifo_in_first;
wire clockdomaincrossing4_cdc_fifo_in_last;
wire [1:0] clockdomaincrossing4_cdc_fifo_out_payload_resp;
wire [31:0] clockdomaincrossing4_cdc_fifo_out_payload_data;
wire clockdomaincrossing4_cdc_fifo_out_first;
wire clockdomaincrossing4_cdc_fifo_out_last;
wire rst_meta0;
wire rst_meta1;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl00 = 3'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl01 = 3'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl10 = 3'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl11 = 3'd0;
wire rst_meta2;
wire rst_meta3;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl20 = 3'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl21 = 3'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl30 = 3'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl31 = 3'd0;
wire rst_meta4;
wire rst_meta5;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl40 = 3'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl41 = 3'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl50 = 3'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl51 = 3'd0;
wire rst_meta6;
wire rst_meta7;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl60 = 3'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl61 = 3'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl70 = 3'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl71 = 3'd0;
wire rst_meta8;
wire rst_meta9;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl80 = 3'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl81 = 3'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl90 = 3'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg [2:0] xilinxmultiregimpl91 = 3'd0;

// synthesis translate_off
reg dummy_s;
initial dummy_s <= 1'd0;
// synthesis translate_on

assign {{ps_aw_payload_prot, ps_aw_payload_addr}, ps_aw_last, ps_aw_first} = aw_input;
assign aw_output = {{tx_aw_payload_prot, tx_aw_payload_addr}, tx_aw_last, tx_aw_first};
assign {{ps_w_payload_strb, ps_w_payload_data}, ps_w_last, ps_w_first} = w_input;
assign w_output = {{tx_w_payload_strb, tx_w_payload_data}, tx_w_last, tx_w_first};
assign {{tx_b_payload_resp}, tx_b_last, tx_b_first} = b_input;
assign b_output = {{ps_b_payload_resp}, ps_b_last, ps_b_first};
assign {{ps_ar_payload_prot, ps_ar_payload_addr}, ps_ar_last, ps_ar_first} = ar_input;
assign ar_output = {{tx_ar_payload_prot, tx_ar_payload_addr}, tx_ar_last, tx_ar_first};
assign {{tx_r_payload_data, tx_r_payload_resp}, tx_r_last, tx_r_first} = r_input;
assign r_output = {{ps_r_payload_data, ps_r_payload_resp}, ps_r_last, ps_r_first};

// synthesis translate_off
reg dummy_d;
// synthesis translate_on
always @(*) begin
	private_resets <= 10'd0;
	private_resets[0] <= from126_rst;
	private_resets[1] <= to126_rst;
	private_resets[2] <= from289_rst;
	private_resets[3] <= to289_rst;
	private_resets[4] <= from452_rst;
	private_resets[5] <= to452_rst;
	private_resets[6] <= from603_rst;
	private_resets[7] <= to603_rst;
	private_resets[8] <= from766_rst;
	private_resets[9] <= to766_rst;
// synthesis translate_off
	dummy_d <= dummy_s;
// synthesis translate_on
end
assign clockdomaincrossing0_sink_sink_valid = aw_sink_valid;
assign aw_sink_ready = clockdomaincrossing0_sink_sink_ready;
assign clockdomaincrossing0_sink_sink_first = ps_aw_first;
assign clockdomaincrossing0_sink_sink_last = ps_aw_last;
assign clockdomaincrossing0_sink_sink_payload_addr = ps_aw_payload_addr;
assign clockdomaincrossing0_sink_sink_payload_prot = ps_aw_payload_prot;
assign aw_source_valid = clockdomaincrossing0_source_source_valid;
assign clockdomaincrossing0_source_source_ready = aw_source_ready;
assign tx_aw_first = clockdomaincrossing0_source_source_first;
assign tx_aw_last = clockdomaincrossing0_source_source_last;
assign tx_aw_payload_addr = clockdomaincrossing0_source_source_payload_addr;
assign tx_aw_payload_prot = clockdomaincrossing0_source_source_payload_prot;
assign clockdomaincrossing1_sink_sink_valid = w_sink_valid;
assign w_sink_ready = clockdomaincrossing1_sink_sink_ready;
assign clockdomaincrossing1_sink_sink_first = ps_w_first;
assign clockdomaincrossing1_sink_sink_last = ps_w_last;
assign clockdomaincrossing1_sink_sink_payload_data = ps_w_payload_data;
assign clockdomaincrossing1_sink_sink_payload_strb = ps_w_payload_strb;
assign w_source_valid = clockdomaincrossing1_source_source_valid;
assign clockdomaincrossing1_source_source_ready = w_source_ready;
assign tx_w_first = clockdomaincrossing1_source_source_first;
assign tx_w_last = clockdomaincrossing1_source_source_last;
assign tx_w_payload_data = clockdomaincrossing1_source_source_payload_data;
assign tx_w_payload_strb = clockdomaincrossing1_source_source_payload_strb;
assign clockdomaincrossing2_sink_sink_valid = b_sink_valid;
assign b_sink_ready = clockdomaincrossing2_sink_sink_ready;
assign clockdomaincrossing2_sink_sink_first = tx_b_first;
assign clockdomaincrossing2_sink_sink_last = tx_b_last;
assign clockdomaincrossing2_sink_sink_payload_resp = tx_b_payload_resp;
assign b_source_valid = clockdomaincrossing2_source_source_valid;
assign clockdomaincrossing2_source_source_ready = b_source_ready;
assign ps_b_first = clockdomaincrossing2_source_source_first;
assign ps_b_last = clockdomaincrossing2_source_source_last;
assign ps_b_payload_resp = clockdomaincrossing2_source_source_payload_resp;
assign clockdomaincrossing3_sink_sink_valid = ar_sink_valid;
assign ar_sink_ready = clockdomaincrossing3_sink_sink_ready;
assign clockdomaincrossing3_sink_sink_first = ps_ar_first;
assign clockdomaincrossing3_sink_sink_last = ps_ar_last;
assign clockdomaincrossing3_sink_sink_payload_addr = ps_ar_payload_addr;
assign clockdomaincrossing3_sink_sink_payload_prot = ps_ar_payload_prot;
assign ar_source_valid = clockdomaincrossing3_source_source_valid;
assign clockdomaincrossing3_source_source_ready = ar_source_ready;
assign tx_ar_first = clockdomaincrossing3_source_source_first;
assign tx_ar_last = clockdomaincrossing3_source_source_last;
assign tx_ar_payload_addr = clockdomaincrossing3_source_source_payload_addr;
assign tx_ar_payload_prot = clockdomaincrossing3_source_source_payload_prot;
assign clockdomaincrossing4_sink_sink_valid = r_sink_valid;
assign r_sink_ready = clockdomaincrossing4_sink_sink_ready;
assign clockdomaincrossing4_sink_sink_first = tx_r_first;
assign clockdomaincrossing4_sink_sink_last = tx_r_last;
assign clockdomaincrossing4_sink_sink_payload_resp = tx_r_payload_resp;
assign clockdomaincrossing4_sink_sink_payload_data = tx_r_payload_data;
assign r_source_valid = clockdomaincrossing4_source_source_valid;
assign clockdomaincrossing4_source_source_ready = r_source_ready;
assign ps_r_first = clockdomaincrossing4_source_source_first;
assign ps_r_last = clockdomaincrossing4_source_source_last;
assign ps_r_payload_resp = clockdomaincrossing4_source_source_payload_resp;
assign ps_r_payload_data = clockdomaincrossing4_source_source_payload_data;
assign from126_clk = ps_clock;
assign to126_clk = tx_clock;
assign clockdomaincrossing0_cd_rst = (ps_reset | tx_reset);
assign clockdomaincrossing0_cdc_sink_valid = clockdomaincrossing0_sink_sink_valid;
assign clockdomaincrossing0_sink_sink_ready = clockdomaincrossing0_cdc_sink_ready;
assign clockdomaincrossing0_cdc_sink_first = clockdomaincrossing0_sink_sink_first;
assign clockdomaincrossing0_cdc_sink_last = clockdomaincrossing0_sink_sink_last;
assign clockdomaincrossing0_cdc_sink_payload_addr = clockdomaincrossing0_sink_sink_payload_addr;
assign clockdomaincrossing0_cdc_sink_payload_prot = clockdomaincrossing0_sink_sink_payload_prot;
assign clockdomaincrossing0_source_source_valid = clockdomaincrossing0_cdc_source_valid;
assign clockdomaincrossing0_cdc_source_ready = clockdomaincrossing0_source_source_ready;
assign clockdomaincrossing0_source_source_first = clockdomaincrossing0_cdc_source_first;
assign clockdomaincrossing0_source_source_last = clockdomaincrossing0_cdc_source_last;
assign clockdomaincrossing0_source_source_payload_addr = clockdomaincrossing0_cdc_source_payload_addr;
assign clockdomaincrossing0_source_source_payload_prot = clockdomaincrossing0_cdc_source_payload_prot;
assign clockdomaincrossing0_cdc_asyncfifo0_din = {clockdomaincrossing0_cdc_fifo_in_last, clockdomaincrossing0_cdc_fifo_in_first, clockdomaincrossing0_cdc_fifo_in_payload_prot, clockdomaincrossing0_cdc_fifo_in_payload_addr};
assign {clockdomaincrossing0_cdc_fifo_out_last, clockdomaincrossing0_cdc_fifo_out_first, clockdomaincrossing0_cdc_fifo_out_payload_prot, clockdomaincrossing0_cdc_fifo_out_payload_addr} = clockdomaincrossing0_cdc_asyncfifo0_dout;
assign clockdomaincrossing0_cdc_sink_ready = clockdomaincrossing0_cdc_asyncfifo0_writable;
assign clockdomaincrossing0_cdc_asyncfifo0_we = clockdomaincrossing0_cdc_sink_valid;
assign clockdomaincrossing0_cdc_fifo_in_first = clockdomaincrossing0_cdc_sink_first;
assign clockdomaincrossing0_cdc_fifo_in_last = clockdomaincrossing0_cdc_sink_last;
assign clockdomaincrossing0_cdc_fifo_in_payload_addr = clockdomaincrossing0_cdc_sink_payload_addr;
assign clockdomaincrossing0_cdc_fifo_in_payload_prot = clockdomaincrossing0_cdc_sink_payload_prot;
assign clockdomaincrossing0_cdc_source_valid = clockdomaincrossing0_cdc_asyncfifo0_readable;
assign clockdomaincrossing0_cdc_source_first = clockdomaincrossing0_cdc_fifo_out_first;
assign clockdomaincrossing0_cdc_source_last = clockdomaincrossing0_cdc_fifo_out_last;
assign clockdomaincrossing0_cdc_source_payload_addr = clockdomaincrossing0_cdc_fifo_out_payload_addr;
assign clockdomaincrossing0_cdc_source_payload_prot = clockdomaincrossing0_cdc_fifo_out_payload_prot;
assign clockdomaincrossing0_cdc_asyncfifo0_re = clockdomaincrossing0_cdc_source_ready;
assign clockdomaincrossing0_cdc_graycounter0_ce = (clockdomaincrossing0_cdc_asyncfifo0_writable & clockdomaincrossing0_cdc_asyncfifo0_we);
assign clockdomaincrossing0_cdc_graycounter1_ce = (clockdomaincrossing0_cdc_asyncfifo0_readable & clockdomaincrossing0_cdc_asyncfifo0_re);
assign clockdomaincrossing0_cdc_asyncfifo0_writable = (((clockdomaincrossing0_cdc_graycounter0_q[2] == clockdomaincrossing0_cdc_consume_wdomain[2]) | (clockdomaincrossing0_cdc_graycounter0_q[1] == clockdomaincrossing0_cdc_consume_wdomain[1])) | (clockdomaincrossing0_cdc_graycounter0_q[0] != clockdomaincrossing0_cdc_consume_wdomain[0]));
assign clockdomaincrossing0_cdc_asyncfifo0_readable = (clockdomaincrossing0_cdc_graycounter1_q != clockdomaincrossing0_cdc_produce_rdomain);
assign clockdomaincrossing0_cdc_wrport_adr = clockdomaincrossing0_cdc_graycounter0_q_binary[1:0];
assign clockdomaincrossing0_cdc_wrport_dat_w = clockdomaincrossing0_cdc_asyncfifo0_din;
assign clockdomaincrossing0_cdc_wrport_we = clockdomaincrossing0_cdc_graycounter0_ce;
assign clockdomaincrossing0_cdc_rdport_adr = clockdomaincrossing0_cdc_graycounter1_q_next_binary[1:0];
assign clockdomaincrossing0_cdc_asyncfifo0_dout = clockdomaincrossing0_cdc_rdport_dat_r;

// synthesis translate_off
reg dummy_d_1;
// synthesis translate_on
always @(*) begin
	clockdomaincrossing0_cdc_graycounter0_q_next_binary <= 3'd0;
	if (clockdomaincrossing0_cdc_graycounter0_ce) begin
		clockdomaincrossing0_cdc_graycounter0_q_next_binary <= (clockdomaincrossing0_cdc_graycounter0_q_binary + 1'd1);
	end else begin
		clockdomaincrossing0_cdc_graycounter0_q_next_binary <= clockdomaincrossing0_cdc_graycounter0_q_binary;
	end
// synthesis translate_off
	dummy_d_1 <= dummy_s;
// synthesis translate_on
end
assign clockdomaincrossing0_cdc_graycounter0_q_next = (clockdomaincrossing0_cdc_graycounter0_q_next_binary ^ clockdomaincrossing0_cdc_graycounter0_q_next_binary[2:1]);

// synthesis translate_off
reg dummy_d_2;
// synthesis translate_on
always @(*) begin
	clockdomaincrossing0_cdc_graycounter1_q_next_binary <= 3'd0;
	if (clockdomaincrossing0_cdc_graycounter1_ce) begin
		clockdomaincrossing0_cdc_graycounter1_q_next_binary <= (clockdomaincrossing0_cdc_graycounter1_q_binary + 1'd1);
	end else begin
		clockdomaincrossing0_cdc_graycounter1_q_next_binary <= clockdomaincrossing0_cdc_graycounter1_q_binary;
	end
// synthesis translate_off
	dummy_d_2 <= dummy_s;
// synthesis translate_on
end
assign clockdomaincrossing0_cdc_graycounter1_q_next = (clockdomaincrossing0_cdc_graycounter1_q_next_binary ^ clockdomaincrossing0_cdc_graycounter1_q_next_binary[2:1]);
assign from289_clk = ps_clock;
assign to289_clk = tx_clock;
assign clockdomaincrossing1_cd_rst = (ps_reset | tx_reset);
assign clockdomaincrossing1_cdc_sink_valid = clockdomaincrossing1_sink_sink_valid;
assign clockdomaincrossing1_sink_sink_ready = clockdomaincrossing1_cdc_sink_ready;
assign clockdomaincrossing1_cdc_sink_first = clockdomaincrossing1_sink_sink_first;
assign clockdomaincrossing1_cdc_sink_last = clockdomaincrossing1_sink_sink_last;
assign clockdomaincrossing1_cdc_sink_payload_data = clockdomaincrossing1_sink_sink_payload_data;
assign clockdomaincrossing1_cdc_sink_payload_strb = clockdomaincrossing1_sink_sink_payload_strb;
assign clockdomaincrossing1_source_source_valid = clockdomaincrossing1_cdc_source_valid;
assign clockdomaincrossing1_cdc_source_ready = clockdomaincrossing1_source_source_ready;
assign clockdomaincrossing1_source_source_first = clockdomaincrossing1_cdc_source_first;
assign clockdomaincrossing1_source_source_last = clockdomaincrossing1_cdc_source_last;
assign clockdomaincrossing1_source_source_payload_data = clockdomaincrossing1_cdc_source_payload_data;
assign clockdomaincrossing1_source_source_payload_strb = clockdomaincrossing1_cdc_source_payload_strb;
assign clockdomaincrossing1_cdc_asyncfifo1_din = {clockdomaincrossing1_cdc_fifo_in_last, clockdomaincrossing1_cdc_fifo_in_first, clockdomaincrossing1_cdc_fifo_in_payload_strb, clockdomaincrossing1_cdc_fifo_in_payload_data};
assign {clockdomaincrossing1_cdc_fifo_out_last, clockdomaincrossing1_cdc_fifo_out_first, clockdomaincrossing1_cdc_fifo_out_payload_strb, clockdomaincrossing1_cdc_fifo_out_payload_data} = clockdomaincrossing1_cdc_asyncfifo1_dout;
assign clockdomaincrossing1_cdc_sink_ready = clockdomaincrossing1_cdc_asyncfifo1_writable;
assign clockdomaincrossing1_cdc_asyncfifo1_we = clockdomaincrossing1_cdc_sink_valid;
assign clockdomaincrossing1_cdc_fifo_in_first = clockdomaincrossing1_cdc_sink_first;
assign clockdomaincrossing1_cdc_fifo_in_last = clockdomaincrossing1_cdc_sink_last;
assign clockdomaincrossing1_cdc_fifo_in_payload_data = clockdomaincrossing1_cdc_sink_payload_data;
assign clockdomaincrossing1_cdc_fifo_in_payload_strb = clockdomaincrossing1_cdc_sink_payload_strb;
assign clockdomaincrossing1_cdc_source_valid = clockdomaincrossing1_cdc_asyncfifo1_readable;
assign clockdomaincrossing1_cdc_source_first = clockdomaincrossing1_cdc_fifo_out_first;
assign clockdomaincrossing1_cdc_source_last = clockdomaincrossing1_cdc_fifo_out_last;
assign clockdomaincrossing1_cdc_source_payload_data = clockdomaincrossing1_cdc_fifo_out_payload_data;
assign clockdomaincrossing1_cdc_source_payload_strb = clockdomaincrossing1_cdc_fifo_out_payload_strb;
assign clockdomaincrossing1_cdc_asyncfifo1_re = clockdomaincrossing1_cdc_source_ready;
assign clockdomaincrossing1_cdc_graycounter2_ce = (clockdomaincrossing1_cdc_asyncfifo1_writable & clockdomaincrossing1_cdc_asyncfifo1_we);
assign clockdomaincrossing1_cdc_graycounter3_ce = (clockdomaincrossing1_cdc_asyncfifo1_readable & clockdomaincrossing1_cdc_asyncfifo1_re);
assign clockdomaincrossing1_cdc_asyncfifo1_writable = (((clockdomaincrossing1_cdc_graycounter2_q[2] == clockdomaincrossing1_cdc_consume_wdomain[2]) | (clockdomaincrossing1_cdc_graycounter2_q[1] == clockdomaincrossing1_cdc_consume_wdomain[1])) | (clockdomaincrossing1_cdc_graycounter2_q[0] != clockdomaincrossing1_cdc_consume_wdomain[0]));
assign clockdomaincrossing1_cdc_asyncfifo1_readable = (clockdomaincrossing1_cdc_graycounter3_q != clockdomaincrossing1_cdc_produce_rdomain);
assign clockdomaincrossing1_cdc_wrport_adr = clockdomaincrossing1_cdc_graycounter2_q_binary[1:0];
assign clockdomaincrossing1_cdc_wrport_dat_w = clockdomaincrossing1_cdc_asyncfifo1_din;
assign clockdomaincrossing1_cdc_wrport_we = clockdomaincrossing1_cdc_graycounter2_ce;
assign clockdomaincrossing1_cdc_rdport_adr = clockdomaincrossing1_cdc_graycounter3_q_next_binary[1:0];
assign clockdomaincrossing1_cdc_asyncfifo1_dout = clockdomaincrossing1_cdc_rdport_dat_r;

// synthesis translate_off
reg dummy_d_3;
// synthesis translate_on
always @(*) begin
	clockdomaincrossing1_cdc_graycounter2_q_next_binary <= 3'd0;
	if (clockdomaincrossing1_cdc_graycounter2_ce) begin
		clockdomaincrossing1_cdc_graycounter2_q_next_binary <= (clockdomaincrossing1_cdc_graycounter2_q_binary + 1'd1);
	end else begin
		clockdomaincrossing1_cdc_graycounter2_q_next_binary <= clockdomaincrossing1_cdc_graycounter2_q_binary;
	end
// synthesis translate_off
	dummy_d_3 <= dummy_s;
// synthesis translate_on
end
assign clockdomaincrossing1_cdc_graycounter2_q_next = (clockdomaincrossing1_cdc_graycounter2_q_next_binary ^ clockdomaincrossing1_cdc_graycounter2_q_next_binary[2:1]);

// synthesis translate_off
reg dummy_d_4;
// synthesis translate_on
always @(*) begin
	clockdomaincrossing1_cdc_graycounter3_q_next_binary <= 3'd0;
	if (clockdomaincrossing1_cdc_graycounter3_ce) begin
		clockdomaincrossing1_cdc_graycounter3_q_next_binary <= (clockdomaincrossing1_cdc_graycounter3_q_binary + 1'd1);
	end else begin
		clockdomaincrossing1_cdc_graycounter3_q_next_binary <= clockdomaincrossing1_cdc_graycounter3_q_binary;
	end
// synthesis translate_off
	dummy_d_4 <= dummy_s;
// synthesis translate_on
end
assign clockdomaincrossing1_cdc_graycounter3_q_next = (clockdomaincrossing1_cdc_graycounter3_q_next_binary ^ clockdomaincrossing1_cdc_graycounter3_q_next_binary[2:1]);
assign from452_clk = tx_clock;
assign to452_clk = ps_clock;
assign clockdomaincrossing2_cd_rst = (tx_reset | ps_reset);
assign clockdomaincrossing2_cdc_sink_valid = clockdomaincrossing2_sink_sink_valid;
assign clockdomaincrossing2_sink_sink_ready = clockdomaincrossing2_cdc_sink_ready;
assign clockdomaincrossing2_cdc_sink_first = clockdomaincrossing2_sink_sink_first;
assign clockdomaincrossing2_cdc_sink_last = clockdomaincrossing2_sink_sink_last;
assign clockdomaincrossing2_cdc_sink_payload_resp = clockdomaincrossing2_sink_sink_payload_resp;
assign clockdomaincrossing2_source_source_valid = clockdomaincrossing2_cdc_source_valid;
assign clockdomaincrossing2_cdc_source_ready = clockdomaincrossing2_source_source_ready;
assign clockdomaincrossing2_source_source_first = clockdomaincrossing2_cdc_source_first;
assign clockdomaincrossing2_source_source_last = clockdomaincrossing2_cdc_source_last;
assign clockdomaincrossing2_source_source_payload_resp = clockdomaincrossing2_cdc_source_payload_resp;
assign clockdomaincrossing2_cdc_asyncfifo2_din = {clockdomaincrossing2_cdc_fifo_in_last, clockdomaincrossing2_cdc_fifo_in_first, clockdomaincrossing2_cdc_fifo_in_payload_resp};
assign {clockdomaincrossing2_cdc_fifo_out_last, clockdomaincrossing2_cdc_fifo_out_first, clockdomaincrossing2_cdc_fifo_out_payload_resp} = clockdomaincrossing2_cdc_asyncfifo2_dout;
assign clockdomaincrossing2_cdc_sink_ready = clockdomaincrossing2_cdc_asyncfifo2_writable;
assign clockdomaincrossing2_cdc_asyncfifo2_we = clockdomaincrossing2_cdc_sink_valid;
assign clockdomaincrossing2_cdc_fifo_in_first = clockdomaincrossing2_cdc_sink_first;
assign clockdomaincrossing2_cdc_fifo_in_last = clockdomaincrossing2_cdc_sink_last;
assign clockdomaincrossing2_cdc_fifo_in_payload_resp = clockdomaincrossing2_cdc_sink_payload_resp;
assign clockdomaincrossing2_cdc_source_valid = clockdomaincrossing2_cdc_asyncfifo2_readable;
assign clockdomaincrossing2_cdc_source_first = clockdomaincrossing2_cdc_fifo_out_first;
assign clockdomaincrossing2_cdc_source_last = clockdomaincrossing2_cdc_fifo_out_last;
assign clockdomaincrossing2_cdc_source_payload_resp = clockdomaincrossing2_cdc_fifo_out_payload_resp;
assign clockdomaincrossing2_cdc_asyncfifo2_re = clockdomaincrossing2_cdc_source_ready;
assign clockdomaincrossing2_cdc_graycounter4_ce = (clockdomaincrossing2_cdc_asyncfifo2_writable & clockdomaincrossing2_cdc_asyncfifo2_we);
assign clockdomaincrossing2_cdc_graycounter5_ce = (clockdomaincrossing2_cdc_asyncfifo2_readable & clockdomaincrossing2_cdc_asyncfifo2_re);
assign clockdomaincrossing2_cdc_asyncfifo2_writable = (((clockdomaincrossing2_cdc_graycounter4_q[2] == clockdomaincrossing2_cdc_consume_wdomain[2]) | (clockdomaincrossing2_cdc_graycounter4_q[1] == clockdomaincrossing2_cdc_consume_wdomain[1])) | (clockdomaincrossing2_cdc_graycounter4_q[0] != clockdomaincrossing2_cdc_consume_wdomain[0]));
assign clockdomaincrossing2_cdc_asyncfifo2_readable = (clockdomaincrossing2_cdc_graycounter5_q != clockdomaincrossing2_cdc_produce_rdomain);
assign clockdomaincrossing2_cdc_wrport_adr = clockdomaincrossing2_cdc_graycounter4_q_binary[1:0];
assign clockdomaincrossing2_cdc_wrport_dat_w = clockdomaincrossing2_cdc_asyncfifo2_din;
assign clockdomaincrossing2_cdc_wrport_we = clockdomaincrossing2_cdc_graycounter4_ce;
assign clockdomaincrossing2_cdc_rdport_adr = clockdomaincrossing2_cdc_graycounter5_q_next_binary[1:0];
assign clockdomaincrossing2_cdc_asyncfifo2_dout = clockdomaincrossing2_cdc_rdport_dat_r;

// synthesis translate_off
reg dummy_d_5;
// synthesis translate_on
always @(*) begin
	clockdomaincrossing2_cdc_graycounter4_q_next_binary <= 3'd0;
	if (clockdomaincrossing2_cdc_graycounter4_ce) begin
		clockdomaincrossing2_cdc_graycounter4_q_next_binary <= (clockdomaincrossing2_cdc_graycounter4_q_binary + 1'd1);
	end else begin
		clockdomaincrossing2_cdc_graycounter4_q_next_binary <= clockdomaincrossing2_cdc_graycounter4_q_binary;
	end
// synthesis translate_off
	dummy_d_5 <= dummy_s;
// synthesis translate_on
end
assign clockdomaincrossing2_cdc_graycounter4_q_next = (clockdomaincrossing2_cdc_graycounter4_q_next_binary ^ clockdomaincrossing2_cdc_graycounter4_q_next_binary[2:1]);

// synthesis translate_off
reg dummy_d_6;
// synthesis translate_on
always @(*) begin
	clockdomaincrossing2_cdc_graycounter5_q_next_binary <= 3'd0;
	if (clockdomaincrossing2_cdc_graycounter5_ce) begin
		clockdomaincrossing2_cdc_graycounter5_q_next_binary <= (clockdomaincrossing2_cdc_graycounter5_q_binary + 1'd1);
	end else begin
		clockdomaincrossing2_cdc_graycounter5_q_next_binary <= clockdomaincrossing2_cdc_graycounter5_q_binary;
	end
// synthesis translate_off
	dummy_d_6 <= dummy_s;
// synthesis translate_on
end
assign clockdomaincrossing2_cdc_graycounter5_q_next = (clockdomaincrossing2_cdc_graycounter5_q_next_binary ^ clockdomaincrossing2_cdc_graycounter5_q_next_binary[2:1]);
assign from603_clk = ps_clock;
assign to603_clk = tx_clock;
assign clockdomaincrossing3_cd_rst = (ps_reset | tx_reset);
assign clockdomaincrossing3_cdc_sink_valid = clockdomaincrossing3_sink_sink_valid;
assign clockdomaincrossing3_sink_sink_ready = clockdomaincrossing3_cdc_sink_ready;
assign clockdomaincrossing3_cdc_sink_first = clockdomaincrossing3_sink_sink_first;
assign clockdomaincrossing3_cdc_sink_last = clockdomaincrossing3_sink_sink_last;
assign clockdomaincrossing3_cdc_sink_payload_addr = clockdomaincrossing3_sink_sink_payload_addr;
assign clockdomaincrossing3_cdc_sink_payload_prot = clockdomaincrossing3_sink_sink_payload_prot;
assign clockdomaincrossing3_source_source_valid = clockdomaincrossing3_cdc_source_valid;
assign clockdomaincrossing3_cdc_source_ready = clockdomaincrossing3_source_source_ready;
assign clockdomaincrossing3_source_source_first = clockdomaincrossing3_cdc_source_first;
assign clockdomaincrossing3_source_source_last = clockdomaincrossing3_cdc_source_last;
assign clockdomaincrossing3_source_source_payload_addr = clockdomaincrossing3_cdc_source_payload_addr;
assign clockdomaincrossing3_source_source_payload_prot = clockdomaincrossing3_cdc_source_payload_prot;
assign clockdomaincrossing3_cdc_asyncfifo3_din = {clockdomaincrossing3_cdc_fifo_in_last, clockdomaincrossing3_cdc_fifo_in_first, clockdomaincrossing3_cdc_fifo_in_payload_prot, clockdomaincrossing3_cdc_fifo_in_payload_addr};
assign {clockdomaincrossing3_cdc_fifo_out_last, clockdomaincrossing3_cdc_fifo_out_first, clockdomaincrossing3_cdc_fifo_out_payload_prot, clockdomaincrossing3_cdc_fifo_out_payload_addr} = clockdomaincrossing3_cdc_asyncfifo3_dout;
assign clockdomaincrossing3_cdc_sink_ready = clockdomaincrossing3_cdc_asyncfifo3_writable;
assign clockdomaincrossing3_cdc_asyncfifo3_we = clockdomaincrossing3_cdc_sink_valid;
assign clockdomaincrossing3_cdc_fifo_in_first = clockdomaincrossing3_cdc_sink_first;
assign clockdomaincrossing3_cdc_fifo_in_last = clockdomaincrossing3_cdc_sink_last;
assign clockdomaincrossing3_cdc_fifo_in_payload_addr = clockdomaincrossing3_cdc_sink_payload_addr;
assign clockdomaincrossing3_cdc_fifo_in_payload_prot = clockdomaincrossing3_cdc_sink_payload_prot;
assign clockdomaincrossing3_cdc_source_valid = clockdomaincrossing3_cdc_asyncfifo3_readable;
assign clockdomaincrossing3_cdc_source_first = clockdomaincrossing3_cdc_fifo_out_first;
assign clockdomaincrossing3_cdc_source_last = clockdomaincrossing3_cdc_fifo_out_last;
assign clockdomaincrossing3_cdc_source_payload_addr = clockdomaincrossing3_cdc_fifo_out_payload_addr;
assign clockdomaincrossing3_cdc_source_payload_prot = clockdomaincrossing3_cdc_fifo_out_payload_prot;
assign clockdomaincrossing3_cdc_asyncfifo3_re = clockdomaincrossing3_cdc_source_ready;
assign clockdomaincrossing3_cdc_graycounter6_ce = (clockdomaincrossing3_cdc_asyncfifo3_writable & clockdomaincrossing3_cdc_asyncfifo3_we);
assign clockdomaincrossing3_cdc_graycounter7_ce = (clockdomaincrossing3_cdc_asyncfifo3_readable & clockdomaincrossing3_cdc_asyncfifo3_re);
assign clockdomaincrossing3_cdc_asyncfifo3_writable = (((clockdomaincrossing3_cdc_graycounter6_q[2] == clockdomaincrossing3_cdc_consume_wdomain[2]) | (clockdomaincrossing3_cdc_graycounter6_q[1] == clockdomaincrossing3_cdc_consume_wdomain[1])) | (clockdomaincrossing3_cdc_graycounter6_q[0] != clockdomaincrossing3_cdc_consume_wdomain[0]));
assign clockdomaincrossing3_cdc_asyncfifo3_readable = (clockdomaincrossing3_cdc_graycounter7_q != clockdomaincrossing3_cdc_produce_rdomain);
assign clockdomaincrossing3_cdc_wrport_adr = clockdomaincrossing3_cdc_graycounter6_q_binary[1:0];
assign clockdomaincrossing3_cdc_wrport_dat_w = clockdomaincrossing3_cdc_asyncfifo3_din;
assign clockdomaincrossing3_cdc_wrport_we = clockdomaincrossing3_cdc_graycounter6_ce;
assign clockdomaincrossing3_cdc_rdport_adr = clockdomaincrossing3_cdc_graycounter7_q_next_binary[1:0];
assign clockdomaincrossing3_cdc_asyncfifo3_dout = clockdomaincrossing3_cdc_rdport_dat_r;

// synthesis translate_off
reg dummy_d_7;
// synthesis translate_on
always @(*) begin
	clockdomaincrossing3_cdc_graycounter6_q_next_binary <= 3'd0;
	if (clockdomaincrossing3_cdc_graycounter6_ce) begin
		clockdomaincrossing3_cdc_graycounter6_q_next_binary <= (clockdomaincrossing3_cdc_graycounter6_q_binary + 1'd1);
	end else begin
		clockdomaincrossing3_cdc_graycounter6_q_next_binary <= clockdomaincrossing3_cdc_graycounter6_q_binary;
	end
// synthesis translate_off
	dummy_d_7 <= dummy_s;
// synthesis translate_on
end
assign clockdomaincrossing3_cdc_graycounter6_q_next = (clockdomaincrossing3_cdc_graycounter6_q_next_binary ^ clockdomaincrossing3_cdc_graycounter6_q_next_binary[2:1]);

// synthesis translate_off
reg dummy_d_8;
// synthesis translate_on
always @(*) begin
	clockdomaincrossing3_cdc_graycounter7_q_next_binary <= 3'd0;
	if (clockdomaincrossing3_cdc_graycounter7_ce) begin
		clockdomaincrossing3_cdc_graycounter7_q_next_binary <= (clockdomaincrossing3_cdc_graycounter7_q_binary + 1'd1);
	end else begin
		clockdomaincrossing3_cdc_graycounter7_q_next_binary <= clockdomaincrossing3_cdc_graycounter7_q_binary;
	end
// synthesis translate_off
	dummy_d_8 <= dummy_s;
// synthesis translate_on
end
assign clockdomaincrossing3_cdc_graycounter7_q_next = (clockdomaincrossing3_cdc_graycounter7_q_next_binary ^ clockdomaincrossing3_cdc_graycounter7_q_next_binary[2:1]);
assign from766_clk = tx_clock;
assign to766_clk = ps_clock;
assign clockdomaincrossing4_cd_rst = (tx_reset | ps_reset);
assign clockdomaincrossing4_cdc_sink_valid = clockdomaincrossing4_sink_sink_valid;
assign clockdomaincrossing4_sink_sink_ready = clockdomaincrossing4_cdc_sink_ready;
assign clockdomaincrossing4_cdc_sink_first = clockdomaincrossing4_sink_sink_first;
assign clockdomaincrossing4_cdc_sink_last = clockdomaincrossing4_sink_sink_last;
assign clockdomaincrossing4_cdc_sink_payload_resp = clockdomaincrossing4_sink_sink_payload_resp;
assign clockdomaincrossing4_cdc_sink_payload_data = clockdomaincrossing4_sink_sink_payload_data;
assign clockdomaincrossing4_source_source_valid = clockdomaincrossing4_cdc_source_valid;
assign clockdomaincrossing4_cdc_source_ready = clockdomaincrossing4_source_source_ready;
assign clockdomaincrossing4_source_source_first = clockdomaincrossing4_cdc_source_first;
assign clockdomaincrossing4_source_source_last = clockdomaincrossing4_cdc_source_last;
assign clockdomaincrossing4_source_source_payload_resp = clockdomaincrossing4_cdc_source_payload_resp;
assign clockdomaincrossing4_source_source_payload_data = clockdomaincrossing4_cdc_source_payload_data;
assign clockdomaincrossing4_cdc_asyncfifo4_din = {clockdomaincrossing4_cdc_fifo_in_last, clockdomaincrossing4_cdc_fifo_in_first, clockdomaincrossing4_cdc_fifo_in_payload_data, clockdomaincrossing4_cdc_fifo_in_payload_resp};
assign {clockdomaincrossing4_cdc_fifo_out_last, clockdomaincrossing4_cdc_fifo_out_first, clockdomaincrossing4_cdc_fifo_out_payload_data, clockdomaincrossing4_cdc_fifo_out_payload_resp} = clockdomaincrossing4_cdc_asyncfifo4_dout;
assign clockdomaincrossing4_cdc_sink_ready = clockdomaincrossing4_cdc_asyncfifo4_writable;
assign clockdomaincrossing4_cdc_asyncfifo4_we = clockdomaincrossing4_cdc_sink_valid;
assign clockdomaincrossing4_cdc_fifo_in_first = clockdomaincrossing4_cdc_sink_first;
assign clockdomaincrossing4_cdc_fifo_in_last = clockdomaincrossing4_cdc_sink_last;
assign clockdomaincrossing4_cdc_fifo_in_payload_resp = clockdomaincrossing4_cdc_sink_payload_resp;
assign clockdomaincrossing4_cdc_fifo_in_payload_data = clockdomaincrossing4_cdc_sink_payload_data;
assign clockdomaincrossing4_cdc_source_valid = clockdomaincrossing4_cdc_asyncfifo4_readable;
assign clockdomaincrossing4_cdc_source_first = clockdomaincrossing4_cdc_fifo_out_first;
assign clockdomaincrossing4_cdc_source_last = clockdomaincrossing4_cdc_fifo_out_last;
assign clockdomaincrossing4_cdc_source_payload_resp = clockdomaincrossing4_cdc_fifo_out_payload_resp;
assign clockdomaincrossing4_cdc_source_payload_data = clockdomaincrossing4_cdc_fifo_out_payload_data;
assign clockdomaincrossing4_cdc_asyncfifo4_re = clockdomaincrossing4_cdc_source_ready;
assign clockdomaincrossing4_cdc_graycounter8_ce = (clockdomaincrossing4_cdc_asyncfifo4_writable & clockdomaincrossing4_cdc_asyncfifo4_we);
assign clockdomaincrossing4_cdc_graycounter9_ce = (clockdomaincrossing4_cdc_asyncfifo4_readable & clockdomaincrossing4_cdc_asyncfifo4_re);
assign clockdomaincrossing4_cdc_asyncfifo4_writable = (((clockdomaincrossing4_cdc_graycounter8_q[2] == clockdomaincrossing4_cdc_consume_wdomain[2]) | (clockdomaincrossing4_cdc_graycounter8_q[1] == clockdomaincrossing4_cdc_consume_wdomain[1])) | (clockdomaincrossing4_cdc_graycounter8_q[0] != clockdomaincrossing4_cdc_consume_wdomain[0]));
assign clockdomaincrossing4_cdc_asyncfifo4_readable = (clockdomaincrossing4_cdc_graycounter9_q != clockdomaincrossing4_cdc_produce_rdomain);
assign clockdomaincrossing4_cdc_wrport_adr = clockdomaincrossing4_cdc_graycounter8_q_binary[1:0];
assign clockdomaincrossing4_cdc_wrport_dat_w = clockdomaincrossing4_cdc_asyncfifo4_din;
assign clockdomaincrossing4_cdc_wrport_we = clockdomaincrossing4_cdc_graycounter8_ce;
assign clockdomaincrossing4_cdc_rdport_adr = clockdomaincrossing4_cdc_graycounter9_q_next_binary[1:0];
assign clockdomaincrossing4_cdc_asyncfifo4_dout = clockdomaincrossing4_cdc_rdport_dat_r;

// synthesis translate_off
reg dummy_d_9;
// synthesis translate_on
always @(*) begin
	clockdomaincrossing4_cdc_graycounter8_q_next_binary <= 3'd0;
	if (clockdomaincrossing4_cdc_graycounter8_ce) begin
		clockdomaincrossing4_cdc_graycounter8_q_next_binary <= (clockdomaincrossing4_cdc_graycounter8_q_binary + 1'd1);
	end else begin
		clockdomaincrossing4_cdc_graycounter8_q_next_binary <= clockdomaincrossing4_cdc_graycounter8_q_binary;
	end
// synthesis translate_off
	dummy_d_9 <= dummy_s;
// synthesis translate_on
end
assign clockdomaincrossing4_cdc_graycounter8_q_next = (clockdomaincrossing4_cdc_graycounter8_q_next_binary ^ clockdomaincrossing4_cdc_graycounter8_q_next_binary[2:1]);

// synthesis translate_off
reg dummy_d_10;
// synthesis translate_on
always @(*) begin
	clockdomaincrossing4_cdc_graycounter9_q_next_binary <= 3'd0;
	if (clockdomaincrossing4_cdc_graycounter9_ce) begin
		clockdomaincrossing4_cdc_graycounter9_q_next_binary <= (clockdomaincrossing4_cdc_graycounter9_q_binary + 1'd1);
	end else begin
		clockdomaincrossing4_cdc_graycounter9_q_next_binary <= clockdomaincrossing4_cdc_graycounter9_q_binary;
	end
// synthesis translate_off
	dummy_d_10 <= dummy_s;
// synthesis translate_on
end
assign clockdomaincrossing4_cdc_graycounter9_q_next = (clockdomaincrossing4_cdc_graycounter9_q_next_binary ^ clockdomaincrossing4_cdc_graycounter9_q_next_binary[2:1]);
assign clockdomaincrossing0_cdc_produce_rdomain = xilinxmultiregimpl01;
assign clockdomaincrossing0_cdc_consume_wdomain = xilinxmultiregimpl11;
assign clockdomaincrossing1_cdc_produce_rdomain = xilinxmultiregimpl21;
assign clockdomaincrossing1_cdc_consume_wdomain = xilinxmultiregimpl31;
assign clockdomaincrossing2_cdc_produce_rdomain = xilinxmultiregimpl41;
assign clockdomaincrossing2_cdc_consume_wdomain = xilinxmultiregimpl51;
assign clockdomaincrossing3_cdc_produce_rdomain = xilinxmultiregimpl61;
assign clockdomaincrossing3_cdc_consume_wdomain = xilinxmultiregimpl71;
assign clockdomaincrossing4_cdc_produce_rdomain = xilinxmultiregimpl81;
assign clockdomaincrossing4_cdc_consume_wdomain = xilinxmultiregimpl91;

always @(posedge from126_clk) begin
	clockdomaincrossing0_cdc_graycounter0_q_binary <= clockdomaincrossing0_cdc_graycounter0_q_next_binary;
	clockdomaincrossing0_cdc_graycounter0_q <= clockdomaincrossing0_cdc_graycounter0_q_next;
	if (from126_rst) begin
		clockdomaincrossing0_cdc_graycounter0_q <= 3'd0;
		clockdomaincrossing0_cdc_graycounter0_q_binary <= 3'd0;
	end
	xilinxmultiregimpl10 <= clockdomaincrossing0_cdc_graycounter1_q;
	xilinxmultiregimpl11 <= xilinxmultiregimpl10;
end

always @(posedge from289_clk) begin
	clockdomaincrossing1_cdc_graycounter2_q_binary <= clockdomaincrossing1_cdc_graycounter2_q_next_binary;
	clockdomaincrossing1_cdc_graycounter2_q <= clockdomaincrossing1_cdc_graycounter2_q_next;
	if (from289_rst) begin
		clockdomaincrossing1_cdc_graycounter2_q <= 3'd0;
		clockdomaincrossing1_cdc_graycounter2_q_binary <= 3'd0;
	end
	xilinxmultiregimpl30 <= clockdomaincrossing1_cdc_graycounter3_q;
	xilinxmultiregimpl31 <= xilinxmultiregimpl30;
end

always @(posedge from452_clk) begin
	clockdomaincrossing2_cdc_graycounter4_q_binary <= clockdomaincrossing2_cdc_graycounter4_q_next_binary;
	clockdomaincrossing2_cdc_graycounter4_q <= clockdomaincrossing2_cdc_graycounter4_q_next;
	if (from452_rst) begin
		clockdomaincrossing2_cdc_graycounter4_q <= 3'd0;
		clockdomaincrossing2_cdc_graycounter4_q_binary <= 3'd0;
	end
	xilinxmultiregimpl50 <= clockdomaincrossing2_cdc_graycounter5_q;
	xilinxmultiregimpl51 <= xilinxmultiregimpl50;
end

always @(posedge from603_clk) begin
	clockdomaincrossing3_cdc_graycounter6_q_binary <= clockdomaincrossing3_cdc_graycounter6_q_next_binary;
	clockdomaincrossing3_cdc_graycounter6_q <= clockdomaincrossing3_cdc_graycounter6_q_next;
	if (from603_rst) begin
		clockdomaincrossing3_cdc_graycounter6_q <= 3'd0;
		clockdomaincrossing3_cdc_graycounter6_q_binary <= 3'd0;
	end
	xilinxmultiregimpl70 <= clockdomaincrossing3_cdc_graycounter7_q;
	xilinxmultiregimpl71 <= xilinxmultiregimpl70;
end

always @(posedge from766_clk) begin
	clockdomaincrossing4_cdc_graycounter8_q_binary <= clockdomaincrossing4_cdc_graycounter8_q_next_binary;
	clockdomaincrossing4_cdc_graycounter8_q <= clockdomaincrossing4_cdc_graycounter8_q_next;
	if (from766_rst) begin
		clockdomaincrossing4_cdc_graycounter8_q <= 3'd0;
		clockdomaincrossing4_cdc_graycounter8_q_binary <= 3'd0;
	end
	xilinxmultiregimpl90 <= clockdomaincrossing4_cdc_graycounter9_q;
	xilinxmultiregimpl91 <= xilinxmultiregimpl90;
end

always @(posedge to126_clk) begin
	clockdomaincrossing0_cdc_graycounter1_q_binary <= clockdomaincrossing0_cdc_graycounter1_q_next_binary;
	clockdomaincrossing0_cdc_graycounter1_q <= clockdomaincrossing0_cdc_graycounter1_q_next;
	if (to126_rst) begin
		clockdomaincrossing0_cdc_graycounter1_q <= 3'd0;
		clockdomaincrossing0_cdc_graycounter1_q_binary <= 3'd0;
	end
	xilinxmultiregimpl00 <= clockdomaincrossing0_cdc_graycounter0_q;
	xilinxmultiregimpl01 <= xilinxmultiregimpl00;
end

always @(posedge to289_clk) begin
	clockdomaincrossing1_cdc_graycounter3_q_binary <= clockdomaincrossing1_cdc_graycounter3_q_next_binary;
	clockdomaincrossing1_cdc_graycounter3_q <= clockdomaincrossing1_cdc_graycounter3_q_next;
	if (to289_rst) begin
		clockdomaincrossing1_cdc_graycounter3_q <= 3'd0;
		clockdomaincrossing1_cdc_graycounter3_q_binary <= 3'd0;
	end
	xilinxmultiregimpl20 <= clockdomaincrossing1_cdc_graycounter2_q;
	xilinxmultiregimpl21 <= xilinxmultiregimpl20;
end

always @(posedge to452_clk) begin
	clockdomaincrossing2_cdc_graycounter5_q_binary <= clockdomaincrossing2_cdc_graycounter5_q_next_binary;
	clockdomaincrossing2_cdc_graycounter5_q <= clockdomaincrossing2_cdc_graycounter5_q_next;
	if (to452_rst) begin
		clockdomaincrossing2_cdc_graycounter5_q <= 3'd0;
		clockdomaincrossing2_cdc_graycounter5_q_binary <= 3'd0;
	end
	xilinxmultiregimpl40 <= clockdomaincrossing2_cdc_graycounter4_q;
	xilinxmultiregimpl41 <= xilinxmultiregimpl40;
end

always @(posedge to603_clk) begin
	clockdomaincrossing3_cdc_graycounter7_q_binary <= clockdomaincrossing3_cdc_graycounter7_q_next_binary;
	clockdomaincrossing3_cdc_graycounter7_q <= clockdomaincrossing3_cdc_graycounter7_q_next;
	if (to603_rst) begin
		clockdomaincrossing3_cdc_graycounter7_q <= 3'd0;
		clockdomaincrossing3_cdc_graycounter7_q_binary <= 3'd0;
	end
	xilinxmultiregimpl60 <= clockdomaincrossing3_cdc_graycounter6_q;
	xilinxmultiregimpl61 <= xilinxmultiregimpl60;
end

always @(posedge to766_clk) begin
	clockdomaincrossing4_cdc_graycounter9_q_binary <= clockdomaincrossing4_cdc_graycounter9_q_next_binary;
	clockdomaincrossing4_cdc_graycounter9_q <= clockdomaincrossing4_cdc_graycounter9_q_next;
	if (to766_rst) begin
		clockdomaincrossing4_cdc_graycounter9_q <= 3'd0;
		clockdomaincrossing4_cdc_graycounter9_q_binary <= 3'd0;
	end
	xilinxmultiregimpl80 <= clockdomaincrossing4_cdc_graycounter8_q;
	xilinxmultiregimpl81 <= xilinxmultiregimpl80;
end

reg [44:0] storage[0:3];
reg [1:0] memadr;
reg [1:0] memadr_1;
always @(posedge from126_clk) begin : mem_write_block
	if (clockdomaincrossing0_cdc_wrport_we)
		storage[clockdomaincrossing0_cdc_wrport_adr] <= clockdomaincrossing0_cdc_wrport_dat_w;
	memadr <= clockdomaincrossing0_cdc_wrport_adr;
end

always @(posedge to126_clk) begin : mem_write_block_1
	memadr_1 <= clockdomaincrossing0_cdc_rdport_adr;
end

assign clockdomaincrossing0_cdc_wrport_dat_r = storage[memadr];
assign clockdomaincrossing0_cdc_rdport_dat_r = storage[memadr_1];

reg [37:0] storage_1[0:3];
reg [1:0] memadr_2;
reg [1:0] memadr_3;
always @(posedge from289_clk) begin : mem_write_block_2
	if (clockdomaincrossing1_cdc_wrport_we)
		storage_1[clockdomaincrossing1_cdc_wrport_adr] <= clockdomaincrossing1_cdc_wrport_dat_w;
	memadr_2 <= clockdomaincrossing1_cdc_wrport_adr;
end

always @(posedge to289_clk) begin : mem_write_block_3
	memadr_3 <= clockdomaincrossing1_cdc_rdport_adr;
end

assign clockdomaincrossing1_cdc_wrport_dat_r = storage_1[memadr_2];
assign clockdomaincrossing1_cdc_rdport_dat_r = storage_1[memadr_3];

reg [3:0] storage_2[0:3];
reg [1:0] memadr_4;
reg [1:0] memadr_5;
always @(posedge from452_clk) begin : mem_write_block_4
	if (clockdomaincrossing2_cdc_wrport_we)
		storage_2[clockdomaincrossing2_cdc_wrport_adr] <= clockdomaincrossing2_cdc_wrport_dat_w;
	memadr_4 <= clockdomaincrossing2_cdc_wrport_adr;
end

always @(posedge to452_clk) begin : mem_write_block_5
	memadr_5 <= clockdomaincrossing2_cdc_rdport_adr;
end

assign clockdomaincrossing2_cdc_wrport_dat_r = storage_2[memadr_4];
assign clockdomaincrossing2_cdc_rdport_dat_r = storage_2[memadr_5];

reg [44:0] storage_3[0:3];
reg [1:0] memadr_6;
reg [1:0] memadr_7;
always @(posedge from603_clk) begin : mem_write_block_6
	if (clockdomaincrossing3_cdc_wrport_we)
		storage_3[clockdomaincrossing3_cdc_wrport_adr] <= clockdomaincrossing3_cdc_wrport_dat_w;
	memadr_6 <= clockdomaincrossing3_cdc_wrport_adr;
end

always @(posedge to603_clk) begin : mem_write_block_7
	memadr_7 <= clockdomaincrossing3_cdc_rdport_adr;
end

assign clockdomaincrossing3_cdc_wrport_dat_r = storage_3[memadr_6];
assign clockdomaincrossing3_cdc_rdport_dat_r = storage_3[memadr_7];

reg [35:0] storage_4[0:3];
reg [1:0] memadr_8;
reg [1:0] memadr_9;
always @(posedge from766_clk) begin : mem_write_block_8
	if (clockdomaincrossing4_cdc_wrport_we)
		storage_4[clockdomaincrossing4_cdc_wrport_adr] <= clockdomaincrossing4_cdc_wrport_dat_w;
	memadr_8 <= clockdomaincrossing4_cdc_wrport_adr;
end

always @(posedge to766_clk) begin : mem_write_block_9
	memadr_9 <= clockdomaincrossing4_cdc_rdport_adr;
end

assign clockdomaincrossing4_cdc_wrport_dat_r = storage_4[memadr_8];
assign clockdomaincrossing4_cdc_rdport_dat_r = storage_4[memadr_9];

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE (
	.C(from126_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(clockdomaincrossing0_cd_rst),
	.Q(rst_meta0)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_1 (
	.C(from126_clk),
	.CE(1'd1),
	.D(rst_meta0),
	.PRE(clockdomaincrossing0_cd_rst),
	.Q(from126_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_2 (
	.C(to126_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(clockdomaincrossing0_cd_rst),
	.Q(rst_meta1)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_3 (
	.C(to126_clk),
	.CE(1'd1),
	.D(rst_meta1),
	.PRE(clockdomaincrossing0_cd_rst),
	.Q(to126_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_4 (
	.C(from289_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(clockdomaincrossing1_cd_rst),
	.Q(rst_meta2)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_5 (
	.C(from289_clk),
	.CE(1'd1),
	.D(rst_meta2),
	.PRE(clockdomaincrossing1_cd_rst),
	.Q(from289_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_6 (
	.C(to289_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(clockdomaincrossing1_cd_rst),
	.Q(rst_meta3)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_7 (
	.C(to289_clk),
	.CE(1'd1),
	.D(rst_meta3),
	.PRE(clockdomaincrossing1_cd_rst),
	.Q(to289_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_8 (
	.C(from452_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(clockdomaincrossing2_cd_rst),
	.Q(rst_meta4)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_9 (
	.C(from452_clk),
	.CE(1'd1),
	.D(rst_meta4),
	.PRE(clockdomaincrossing2_cd_rst),
	.Q(from452_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_10 (
	.C(to452_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(clockdomaincrossing2_cd_rst),
	.Q(rst_meta5)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_11 (
	.C(to452_clk),
	.CE(1'd1),
	.D(rst_meta5),
	.PRE(clockdomaincrossing2_cd_rst),
	.Q(to452_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_12 (
	.C(from603_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(clockdomaincrossing3_cd_rst),
	.Q(rst_meta6)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_13 (
	.C(from603_clk),
	.CE(1'd1),
	.D(rst_meta6),
	.PRE(clockdomaincrossing3_cd_rst),
	.Q(from603_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_14 (
	.C(to603_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(clockdomaincrossing3_cd_rst),
	.Q(rst_meta7)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_15 (
	.C(to603_clk),
	.CE(1'd1),
	.D(rst_meta7),
	.PRE(clockdomaincrossing3_cd_rst),
	.Q(to603_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_16 (
	.C(from766_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(clockdomaincrossing4_cd_rst),
	.Q(rst_meta8)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_17 (
	.C(from766_clk),
	.CE(1'd1),
	.D(rst_meta8),
	.PRE(clockdomaincrossing4_cd_rst),
	.Q(from766_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_18 (
	.C(to766_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(clockdomaincrossing4_cd_rst),
	.Q(rst_meta9)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_19 (
	.C(to766_clk),
	.CE(1'd1),
	.D(rst_meta9),
	.PRE(clockdomaincrossing4_cd_rst),
	.Q(to766_rst)
);

endmodule
