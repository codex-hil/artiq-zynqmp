`timescale 1ns/1ps
/* Machine-generated using Migen */
module local_reset_parent(
	input pl_clock,
	input tx_clock,
	input rx_clock,
	input pl_resetn,
	output control_reset,
	output sys_reset,
	input request,
	input abandoned,
	output reg coordinator_reset,
	output reg abandon_ready,
	output reg [4:0] domain_ready,
	output reg [4:0] target_reset,
	output allowed
);

wire control_clk;
wire ps_clk;
wire ps_rst;
wire sys_clk;
wire rtio_rx_clk;
wire rtio_rx_rst;
wire rio_clk;
wire rio_rst;
wire rio_phy_clk;
wire rio_phy_rst;
wire [4:0] auxresetcontrol_domain_ready;
wire auxresetcontrol_reset;
wire auxresetcontrol_admit;
wire auxresetcontrol_abandonment_ready;
reg auxresetcontrol_low_seen = 1'd0;
reg auxresetcontrol_abandonment_seen = 1'd0;
reg auxresetcontrol_is_ongoing0;
reg auxresetcontrol_is_ongoing1;
reg auxresetcontrol_is_ongoing2;
reg auxresetcontrol_is_ongoing3;
reg __main___admit = 1'd0;
wire __main___request0;
wire __main___request1;
reg [2:0] __main___ready1;
reg [2:0] __main___reset_out1;
wire aux_release_ps_clk;
wire aux_release_ps_rst;
reg [1:0] __main___count0 = 2'd0;
reg __main___local_ready0 = 1'd0;
wire aux_release_sys_clk;
wire aux_release_sys_rst;
reg [1:0] __main___count1 = 2'd0;
reg __main___local_ready1 = 1'd0;
wire aux_release_rtio_rx_clk;
wire aux_release_rtio_rx_rst;
reg [1:0] __main___count2 = 2'd0;
reg __main___local_ready2 = 1'd0;
reg __main___sample_allowed = 1'd0;
wire codec_rx_reset;
wire codec_rx_reset_done;
wire codec_rx_clock_active;
wire codec_word_aligned;
reg status_reset_done = 1'd1;
reg status_clock_active = 1'd1;
reg status_aligned = 1'd1;
wire __main___boundary_permit;
wire __main___boundary_reset_done;
wire __main___boundary_clock_active;
wire __main___boundary_aligned;
reg [1:0] state = 2'd0;
reg [1:0] next_state;
wire xilinxasyncresetsynchronizerimpl0_async_reset;
wire xilinxasyncresetsynchronizerimpl0_rst_meta;
wire xilinxasyncresetsynchronizerimpl1_rst_meta;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl0_xilinxmultiregimpl00 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl0_xilinxmultiregimpl01 = 1'd0;
wire xilinxmultiregimpl0_i;
wire xilinxasyncresetsynchronizerimpl2_rst_meta;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl1_xilinxmultiregimpl10 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl1_xilinxmultiregimpl11 = 1'd0;
wire xilinxmultiregimpl1_i;
wire xilinxasyncresetsynchronizerimpl3_rst_meta;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl2_xilinxmultiregimpl20 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl2_xilinxmultiregimpl21 = 1'd0;
wire xilinxmultiregimpl2_i;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl30 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl31 = 1'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl40 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl41 = 1'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl50 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl51 = 1'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl60 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl61 = 1'd0;

// synthesis translate_off
reg dummy_s;
initial dummy_s <= 1'd0;
// synthesis translate_on

assign control_clk = pl_clock;
assign ps_clk = pl_clock;
assign sys_clk = tx_clock;
assign rtio_rx_clk = rx_clock;
assign rio_clk = tx_clock;
assign rio_phy_clk = tx_clock;
assign __main___request0 = coordinator_reset;
assign auxresetcontrol_domain_ready = domain_ready;
assign ps_rst = (target_reset[0] | (~pl_resetn));
assign sys_reset = (target_reset[1] | (~pl_resetn));
assign rtio_rx_rst = (target_reset[2] | (~pl_resetn));
assign rio_rst = (target_reset[3] | (~pl_resetn));
assign rio_phy_rst = (target_reset[4] | (~pl_resetn));
assign auxresetcontrol_abandonment_ready = (((auxresetcontrol_is_ongoing0 & (~request)) & auxresetcontrol_low_seen) & (~auxresetcontrol_abandonment_seen));
assign auxresetcontrol_reset = (auxresetcontrol_is_ongoing1 | request);
assign auxresetcontrol_admit = ((auxresetcontrol_is_ongoing2 & (~request)) & (auxresetcontrol_domain_ready == 5'd31));

// synthesis translate_off
reg dummy_d;
// synthesis translate_on
always @(*) begin
	auxresetcontrol_is_ongoing0 <= 1'd0;
	auxresetcontrol_is_ongoing1 <= 1'd0;
	auxresetcontrol_is_ongoing2 <= 1'd0;
	auxresetcontrol_is_ongoing3 <= 1'd0;
	next_state <= 2'd0;
	next_state <= state;
	case (state)
		1'd1: begin
			auxresetcontrol_is_ongoing2 <= 1'd1;
			if (request) begin
				next_state <= 1'd0;
			end
		end
		2'd2: begin
			if (request) begin
				next_state <= 1'd0;
			end else begin
				if ((auxresetcontrol_domain_ready == 5'd31)) begin
					next_state <= 1'd1;
				end
			end
		end
		default: begin
			auxresetcontrol_is_ongoing0 <= 1'd1;
			auxresetcontrol_is_ongoing1 <= 1'd1;
			auxresetcontrol_is_ongoing3 <= 1'd1;
			if ((((~request) & auxresetcontrol_abandonment_seen) & (auxresetcontrol_domain_ready == 1'd0))) begin
				next_state <= 2'd2;
			end
		end
	endcase
// synthesis translate_off
	dummy_d <= dummy_s;
// synthesis translate_on
end
assign __main___request1 = __main___request0;

// synthesis translate_off
reg dummy_d_1;
// synthesis translate_on
always @(*) begin
	domain_ready <= 5'd0;
	domain_ready[0] <= __main___ready1[0];
	domain_ready[1] <= __main___ready1[1];
	domain_ready[2] <= __main___ready1[2];
	domain_ready[3] <= __main___ready1[1];
	domain_ready[4] <= __main___ready1[1];
// synthesis translate_off
	dummy_d_1 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_2;
// synthesis translate_on
always @(*) begin
	target_reset <= 5'd0;
	target_reset[0] <= __main___reset_out1[0];
	target_reset[1] <= __main___reset_out1[1];
	target_reset[2] <= __main___reset_out1[2];
	target_reset[3] <= __main___reset_out1[1];
	target_reset[4] <= __main___reset_out1[1];
// synthesis translate_off
	dummy_d_2 <= dummy_s;
// synthesis translate_on
end
assign aux_release_ps_clk = ps_clk;
assign aux_release_sys_clk = sys_clk;
assign aux_release_rtio_rx_clk = rtio_rx_clk;

// synthesis translate_off
reg dummy_d_3;
// synthesis translate_on
always @(*) begin
	__main___reset_out1 <= 3'd0;
	__main___reset_out1[0] <= aux_release_ps_rst;
	__main___reset_out1[1] <= aux_release_sys_rst;
	__main___reset_out1[2] <= aux_release_rtio_rx_rst;
// synthesis translate_off
	dummy_d_3 <= dummy_s;
// synthesis translate_on
end
assign allowed = (__main___boundary_permit & (~sys_reset));
assign codec_rx_reset = (~allowed);
assign codec_rx_reset_done = __main___boundary_reset_done;
assign codec_rx_clock_active = __main___boundary_clock_active;
assign codec_word_aligned = __main___boundary_aligned;
assign xilinxasyncresetsynchronizerimpl0_async_reset = (~pl_resetn);
assign xilinxmultiregimpl0_i = (__main___local_ready0 & (~aux_release_ps_rst));
assign xilinxmultiregimpl1_i = (__main___local_ready1 & (~aux_release_sys_rst));

// synthesis translate_off
reg dummy_d_4;
// synthesis translate_on
always @(*) begin
	__main___ready1 <= 3'd0;
	__main___ready1[0] <= xilinxmultiregimpl0_xilinxmultiregimpl01;
	__main___ready1[1] <= xilinxmultiregimpl1_xilinxmultiregimpl11;
	__main___ready1[2] <= xilinxmultiregimpl2_xilinxmultiregimpl21;
// synthesis translate_off
	dummy_d_4 <= dummy_s;
// synthesis translate_on
end
assign xilinxmultiregimpl2_i = (__main___local_ready2 & (~aux_release_rtio_rx_rst));
assign __main___boundary_permit = xilinxmultiregimpl31;
assign __main___boundary_reset_done = xilinxmultiregimpl41;
assign __main___boundary_clock_active = xilinxmultiregimpl51;
assign __main___boundary_aligned = xilinxmultiregimpl61;

always @(posedge aux_release_ps_clk) begin
	if ((__main___count0 != 2'd3)) begin
		__main___count0 <= (__main___count0 + 1'd1);
	end else begin
		__main___local_ready0 <= 1'd1;
	end
	if (aux_release_ps_rst) begin
		__main___count0 <= 2'd0;
		__main___local_ready0 <= 1'd0;
	end
end

always @(posedge aux_release_rtio_rx_clk) begin
	if ((__main___count2 != 2'd3)) begin
		__main___count2 <= (__main___count2 + 1'd1);
	end else begin
		__main___local_ready2 <= 1'd1;
	end
	if (aux_release_rtio_rx_rst) begin
		__main___count2 <= 2'd0;
		__main___local_ready2 <= 1'd0;
	end
end

always @(posedge aux_release_sys_clk) begin
	if ((__main___count1 != 2'd3)) begin
		__main___count1 <= (__main___count1 + 1'd1);
	end else begin
		__main___local_ready1 <= 1'd1;
	end
	if (aux_release_sys_rst) begin
		__main___count1 <= 2'd0;
		__main___local_ready1 <= 1'd0;
	end
end

always @(posedge control_clk) begin
	if (request) begin
		auxresetcontrol_low_seen <= 1'd0;
		auxresetcontrol_abandonment_seen <= 1'd0;
	end else begin
		if (auxresetcontrol_is_ongoing3) begin
			if ((~abandoned)) begin
				auxresetcontrol_low_seen <= 1'd1;
			end
			if ((auxresetcontrol_low_seen & abandoned)) begin
				auxresetcontrol_abandonment_seen <= 1'd1;
			end
		end
	end
	state <= next_state;
	coordinator_reset <= auxresetcontrol_reset;
	__main___admit <= (auxresetcontrol_admit & (~auxresetcontrol_reset));
	abandon_ready <= (auxresetcontrol_abandonment_ready & auxresetcontrol_reset);
	__main___sample_allowed <= (__main___admit & (~coordinator_reset));
	if (control_reset) begin
		auxresetcontrol_low_seen <= 1'd0;
		auxresetcontrol_abandonment_seen <= 1'd0;
		coordinator_reset <= 1'd1;
		__main___admit <= 1'd0;
		abandon_ready <= 1'd0;
		__main___sample_allowed <= 1'd0;
		state <= 2'd0;
	end
	xilinxmultiregimpl0_xilinxmultiregimpl00 <= (__main___local_ready0 & (~aux_release_ps_rst));
	xilinxmultiregimpl0_xilinxmultiregimpl01 <= xilinxmultiregimpl0_xilinxmultiregimpl00;
	xilinxmultiregimpl1_xilinxmultiregimpl10 <= (__main___local_ready1 & (~aux_release_sys_rst));
	xilinxmultiregimpl1_xilinxmultiregimpl11 <= xilinxmultiregimpl1_xilinxmultiregimpl10;
	xilinxmultiregimpl2_xilinxmultiregimpl20 <= (__main___local_ready2 & (~aux_release_rtio_rx_rst));
	xilinxmultiregimpl2_xilinxmultiregimpl21 <= xilinxmultiregimpl2_xilinxmultiregimpl20;
end

always @(posedge sys_clk) begin
	xilinxmultiregimpl30 <= __main___sample_allowed;
	xilinxmultiregimpl31 <= xilinxmultiregimpl30;
	xilinxmultiregimpl40 <= status_reset_done;
	xilinxmultiregimpl41 <= xilinxmultiregimpl40;
	xilinxmultiregimpl50 <= status_clock_active;
	xilinxmultiregimpl51 <= xilinxmultiregimpl50;
	xilinxmultiregimpl60 <= status_aligned;
	xilinxmultiregimpl61 <= xilinxmultiregimpl60;
end

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE (
	.C(control_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(xilinxasyncresetsynchronizerimpl0_async_reset),
	.Q(xilinxasyncresetsynchronizerimpl0_rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_1 (
	.C(control_clk),
	.CE(1'd1),
	.D(xilinxasyncresetsynchronizerimpl0_rst_meta),
	.PRE(xilinxasyncresetsynchronizerimpl0_async_reset),
	.Q(control_reset)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_2 (
	.C(aux_release_ps_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(__main___request1),
	.Q(xilinxasyncresetsynchronizerimpl1_rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_3 (
	.C(aux_release_ps_clk),
	.CE(1'd1),
	.D(xilinxasyncresetsynchronizerimpl1_rst_meta),
	.PRE(__main___request1),
	.Q(aux_release_ps_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_4 (
	.C(aux_release_sys_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(__main___request1),
	.Q(xilinxasyncresetsynchronizerimpl2_rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_5 (
	.C(aux_release_sys_clk),
	.CE(1'd1),
	.D(xilinxasyncresetsynchronizerimpl2_rst_meta),
	.PRE(__main___request1),
	.Q(aux_release_sys_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_6 (
	.C(aux_release_rtio_rx_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(__main___request1),
	.Q(xilinxasyncresetsynchronizerimpl3_rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_7 (
	.C(aux_release_rtio_rx_clk),
	.CE(1'd1),
	.D(xilinxasyncresetsynchronizerimpl3_rst_meta),
	.PRE(__main___request1),
	.Q(aux_release_rtio_rx_rst)
);

endmodule
