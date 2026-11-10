`timescale 1ns/1ps
/* Machine-generated using Migen */
module reset_five_domains(
	input management_clock,
	input control_clock,
	input ps_clock,
	input tx_clock,
	input rx_clock,
	output reg [4:0] domain_ready,
	output reg [4:0] target_reset,
	output reg coordinator_reset,
	input request,
	input abandoned,
	output reset_status,
	output abandon_ready,
	output admit
);

wire management_clk;
wire control_clk;
reg control_rst = 1'd0;
wire ps_clk;
wire ps_rst;
wire sys_clk;
wire sys_rst;
wire rtio_rx_clk;
wire rtio_rx_rst;
wire rio_clk;
wire rio_rst;
wire rio_phy_clk;
wire rio_phy_rst;
wire request_1;
wire [4:0] domain_ready_1;
wire requester_abandoned;
wire reset;
wire admit_1;
wire abandonment_ready;
reg low_seen = 1'd0;
reg abandonment_seen = 1'd0;
reg is_ongoing0;
reg is_ongoing1;
reg is_ongoing2;
reg is_ongoing3;
wire releases_request0;
wire releases_request1;
reg [2:0] releases_ready1;
reg [2:0] releases_reset_out1;
wire aux_release_ps_clk;
wire aux_release_ps_rst;
reg [1:0] releases_count0 = 2'd0;
reg releases_local_ready0 = 1'd0;
wire aux_release_sys_clk;
wire aux_release_sys_rst;
reg [1:0] releases_count1 = 2'd0;
reg releases_local_ready1 = 1'd0;
wire aux_release_rtio_rx_clk;
wire aux_release_rtio_rx_rst;
reg [1:0] releases_count2 = 2'd0;
reg releases_local_ready2 = 1'd0;
reg registered_admit = 1'd0;
reg registered_abandonment_ready = 1'd0;
reg [1:0] state = 2'd0;
reg [1:0] next_state;
wire rst_meta0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl0_xilinxmultiregimpl00 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl0_xilinxmultiregimpl01 = 1'd0;
wire xilinxmultiregimpl0_i;
wire rst_meta1;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl1_xilinxmultiregimpl10 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl1_xilinxmultiregimpl11 = 1'd0;
wire xilinxmultiregimpl1_i;
wire rst_meta2;
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
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl70 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl71 = 1'd0;

// synthesis translate_off
reg dummy_s;
initial dummy_s <= 1'd0;
// synthesis translate_on

assign management_clk = management_clock;
assign control_clk = control_clock;
assign ps_clk = ps_clock;
assign sys_clk = tx_clock;
assign rtio_rx_clk = rx_clock;
assign rio_clk = tx_clock;
assign rio_phy_clk = tx_clock;
assign releases_request0 = coordinator_reset;
assign domain_ready_1 = domain_ready;
assign ps_rst = target_reset[0];
assign sys_rst = target_reset[1];
assign rtio_rx_rst = target_reset[2];
assign rio_rst = target_reset[3];
assign rio_phy_rst = target_reset[4];
assign abandonment_ready = (((is_ongoing0 & (~request_1)) & low_seen) & (~abandonment_seen));
assign reset = (is_ongoing1 | request_1);
assign admit_1 = ((is_ongoing2 & (~request_1)) & (domain_ready_1 == 5'd31));

// synthesis translate_off
reg dummy_d;
// synthesis translate_on
always @(*) begin
	is_ongoing0 <= 1'd0;
	is_ongoing1 <= 1'd0;
	is_ongoing2 <= 1'd0;
	is_ongoing3 <= 1'd0;
	next_state <= 2'd0;
	next_state <= state;
	case (state)
		1'd1: begin
			is_ongoing2 <= 1'd1;
			if (request_1) begin
				next_state <= 1'd0;
			end
		end
		2'd2: begin
			if (request_1) begin
				next_state <= 1'd0;
			end else begin
				if ((domain_ready_1 == 5'd31)) begin
					next_state <= 1'd1;
				end
			end
		end
		default: begin
			is_ongoing0 <= 1'd1;
			is_ongoing1 <= 1'd1;
			is_ongoing3 <= 1'd1;
			if ((((~request_1) & abandonment_seen) & (domain_ready_1 == 1'd0))) begin
				next_state <= 2'd2;
			end
		end
	endcase
// synthesis translate_off
	dummy_d <= dummy_s;
// synthesis translate_on
end
assign releases_request1 = releases_request0;

// synthesis translate_off
reg dummy_d_1;
// synthesis translate_on
always @(*) begin
	domain_ready <= 5'd0;
	domain_ready[0] <= releases_ready1[0];
	domain_ready[1] <= releases_ready1[1];
	domain_ready[2] <= releases_ready1[2];
	domain_ready[3] <= releases_ready1[1];
	domain_ready[4] <= releases_ready1[1];
// synthesis translate_off
	dummy_d_1 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_2;
// synthesis translate_on
always @(*) begin
	target_reset <= 5'd0;
	target_reset[0] <= releases_reset_out1[0];
	target_reset[1] <= releases_reset_out1[1];
	target_reset[2] <= releases_reset_out1[2];
	target_reset[3] <= releases_reset_out1[1];
	target_reset[4] <= releases_reset_out1[1];
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
	releases_reset_out1 <= 3'd0;
	releases_reset_out1[0] <= aux_release_ps_rst;
	releases_reset_out1[1] <= aux_release_sys_rst;
	releases_reset_out1[2] <= aux_release_rtio_rx_rst;
// synthesis translate_off
	dummy_d_3 <= dummy_s;
// synthesis translate_on
end
assign xilinxmultiregimpl0_i = (releases_local_ready0 & (~aux_release_ps_rst));
assign xilinxmultiregimpl1_i = (releases_local_ready1 & (~aux_release_sys_rst));

// synthesis translate_off
reg dummy_d_4;
// synthesis translate_on
always @(*) begin
	releases_ready1 <= 3'd0;
	releases_ready1[0] <= xilinxmultiregimpl0_xilinxmultiregimpl01;
	releases_ready1[1] <= xilinxmultiregimpl1_xilinxmultiregimpl11;
	releases_ready1[2] <= xilinxmultiregimpl2_xilinxmultiregimpl21;
// synthesis translate_off
	dummy_d_4 <= dummy_s;
// synthesis translate_on
end
assign xilinxmultiregimpl2_i = (releases_local_ready2 & (~aux_release_rtio_rx_rst));
assign request_1 = xilinxmultiregimpl31;
assign requester_abandoned = xilinxmultiregimpl41;
assign reset_status = xilinxmultiregimpl51;
assign abandon_ready = xilinxmultiregimpl61;
assign admit = xilinxmultiregimpl71;

always @(posedge aux_release_ps_clk) begin
	if ((releases_count0 != 2'd3)) begin
		releases_count0 <= (releases_count0 + 1'd1);
	end else begin
		releases_local_ready0 <= 1'd1;
	end
	if (aux_release_ps_rst) begin
		releases_count0 <= 2'd0;
		releases_local_ready0 <= 1'd0;
	end
end

always @(posedge aux_release_rtio_rx_clk) begin
	if ((releases_count2 != 2'd3)) begin
		releases_count2 <= (releases_count2 + 1'd1);
	end else begin
		releases_local_ready2 <= 1'd1;
	end
	if (aux_release_rtio_rx_rst) begin
		releases_count2 <= 2'd0;
		releases_local_ready2 <= 1'd0;
	end
end

always @(posedge aux_release_sys_clk) begin
	if ((releases_count1 != 2'd3)) begin
		releases_count1 <= (releases_count1 + 1'd1);
	end else begin
		releases_local_ready1 <= 1'd1;
	end
	if (aux_release_sys_rst) begin
		releases_count1 <= 2'd0;
		releases_local_ready1 <= 1'd0;
	end
end

always @(posedge control_clk) begin
	if (request_1) begin
		low_seen <= 1'd0;
		abandonment_seen <= 1'd0;
	end else begin
		if (is_ongoing3) begin
			if ((~requester_abandoned)) begin
				low_seen <= 1'd1;
			end
			if ((low_seen & requester_abandoned)) begin
				abandonment_seen <= 1'd1;
			end
		end
	end
	state <= next_state;
	coordinator_reset <= reset;
	registered_admit <= (admit_1 & (~reset));
	registered_abandonment_ready <= (abandonment_ready & reset);
	if (control_rst) begin
		low_seen <= 1'd0;
		abandonment_seen <= 1'd0;
		coordinator_reset <= 1'd1;
		registered_admit <= 1'd0;
		registered_abandonment_ready <= 1'd0;
		state <= 2'd0;
	end
	xilinxmultiregimpl0_xilinxmultiregimpl00 <= (releases_local_ready0 & (~aux_release_ps_rst));
	xilinxmultiregimpl0_xilinxmultiregimpl01 <= xilinxmultiregimpl0_xilinxmultiregimpl00;
	xilinxmultiregimpl1_xilinxmultiregimpl10 <= (releases_local_ready1 & (~aux_release_sys_rst));
	xilinxmultiregimpl1_xilinxmultiregimpl11 <= xilinxmultiregimpl1_xilinxmultiregimpl10;
	xilinxmultiregimpl2_xilinxmultiregimpl20 <= (releases_local_ready2 & (~aux_release_rtio_rx_rst));
	xilinxmultiregimpl2_xilinxmultiregimpl21 <= xilinxmultiregimpl2_xilinxmultiregimpl20;
	xilinxmultiregimpl30 <= request;
	xilinxmultiregimpl31 <= xilinxmultiregimpl30;
	xilinxmultiregimpl40 <= abandoned;
	xilinxmultiregimpl41 <= xilinxmultiregimpl40;
end

always @(posedge management_clk) begin
	xilinxmultiregimpl50 <= coordinator_reset;
	xilinxmultiregimpl51 <= xilinxmultiregimpl50;
	xilinxmultiregimpl60 <= registered_abandonment_ready;
	xilinxmultiregimpl61 <= xilinxmultiregimpl60;
	xilinxmultiregimpl70 <= registered_admit;
	xilinxmultiregimpl71 <= xilinxmultiregimpl70;
end

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE (
	.C(aux_release_ps_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(releases_request1),
	.Q(rst_meta0)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_1 (
	.C(aux_release_ps_clk),
	.CE(1'd1),
	.D(rst_meta0),
	.PRE(releases_request1),
	.Q(aux_release_ps_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_2 (
	.C(aux_release_sys_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(releases_request1),
	.Q(rst_meta1)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_3 (
	.C(aux_release_sys_clk),
	.CE(1'd1),
	.D(rst_meta1),
	.PRE(releases_request1),
	.Q(aux_release_sys_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_4 (
	.C(aux_release_rtio_rx_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(releases_request1),
	.Q(rst_meta2)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_5 (
	.C(aux_release_rtio_rx_clk),
	.CE(1'd1),
	.D(rst_meta2),
	.PRE(releases_request1),
	.Q(aux_release_rtio_rx_rst)
);

endmodule
