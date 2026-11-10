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
wire releases_request;
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
wire aux_release_rio_clk;
wire aux_release_rio_rst;
reg [1:0] releases_count3 = 2'd0;
reg releases_local_ready3 = 1'd0;
wire aux_release_rio_phy_clk;
wire aux_release_rio_phy_rst;
reg [1:0] releases_count4 = 2'd0;
reg releases_local_ready4 = 1'd0;
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
wire rst_meta3;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl3_xilinxmultiregimpl30 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl3_xilinxmultiregimpl31 = 1'd0;
wire xilinxmultiregimpl3_i;
wire rst_meta4;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl4_xilinxmultiregimpl40 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl4_xilinxmultiregimpl41 = 1'd0;
wire xilinxmultiregimpl4_i;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl50 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl51 = 1'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl60 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl61 = 1'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl70 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl71 = 1'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl80 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl81 = 1'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl90 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl91 = 1'd0;

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
assign releases_request = coordinator_reset;
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
assign aux_release_ps_clk = ps_clk;
assign aux_release_sys_clk = sys_clk;
assign aux_release_rtio_rx_clk = rtio_rx_clk;
assign aux_release_rio_clk = rio_clk;
assign aux_release_rio_phy_clk = rio_phy_clk;

// synthesis translate_off
reg dummy_d_1;
// synthesis translate_on
always @(*) begin
	target_reset <= 5'd0;
	target_reset[0] <= aux_release_ps_rst;
	target_reset[1] <= aux_release_sys_rst;
	target_reset[2] <= aux_release_rtio_rx_rst;
	target_reset[3] <= aux_release_rio_rst;
	target_reset[4] <= aux_release_rio_phy_rst;
// synthesis translate_off
	dummy_d_1 <= dummy_s;
// synthesis translate_on
end
assign xilinxmultiregimpl0_i = (releases_local_ready0 & (~aux_release_ps_rst));
assign xilinxmultiregimpl1_i = (releases_local_ready1 & (~aux_release_sys_rst));
assign xilinxmultiregimpl2_i = (releases_local_ready2 & (~aux_release_rtio_rx_rst));
assign xilinxmultiregimpl3_i = (releases_local_ready3 & (~aux_release_rio_rst));

// synthesis translate_off
reg dummy_d_2;
// synthesis translate_on
always @(*) begin
	domain_ready <= 5'd0;
	domain_ready[0] <= xilinxmultiregimpl0_xilinxmultiregimpl01;
	domain_ready[1] <= xilinxmultiregimpl1_xilinxmultiregimpl11;
	domain_ready[2] <= xilinxmultiregimpl2_xilinxmultiregimpl21;
	domain_ready[3] <= xilinxmultiregimpl3_xilinxmultiregimpl31;
	domain_ready[4] <= xilinxmultiregimpl4_xilinxmultiregimpl41;
// synthesis translate_off
	dummy_d_2 <= dummy_s;
// synthesis translate_on
end
assign xilinxmultiregimpl4_i = (releases_local_ready4 & (~aux_release_rio_phy_rst));
assign request_1 = xilinxmultiregimpl51;
assign requester_abandoned = xilinxmultiregimpl61;
assign reset_status = xilinxmultiregimpl71;
assign abandon_ready = xilinxmultiregimpl81;
assign admit = xilinxmultiregimpl91;

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

always @(posedge aux_release_rio_clk) begin
	if ((releases_count3 != 2'd3)) begin
		releases_count3 <= (releases_count3 + 1'd1);
	end else begin
		releases_local_ready3 <= 1'd1;
	end
	if (aux_release_rio_rst) begin
		releases_count3 <= 2'd0;
		releases_local_ready3 <= 1'd0;
	end
end

always @(posedge aux_release_rio_phy_clk) begin
	if ((releases_count4 != 2'd3)) begin
		releases_count4 <= (releases_count4 + 1'd1);
	end else begin
		releases_local_ready4 <= 1'd1;
	end
	if (aux_release_rio_phy_rst) begin
		releases_count4 <= 2'd0;
		releases_local_ready4 <= 1'd0;
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
	xilinxmultiregimpl3_xilinxmultiregimpl30 <= (releases_local_ready3 & (~aux_release_rio_rst));
	xilinxmultiregimpl3_xilinxmultiregimpl31 <= xilinxmultiregimpl3_xilinxmultiregimpl30;
	xilinxmultiregimpl4_xilinxmultiregimpl40 <= (releases_local_ready4 & (~aux_release_rio_phy_rst));
	xilinxmultiregimpl4_xilinxmultiregimpl41 <= xilinxmultiregimpl4_xilinxmultiregimpl40;
	xilinxmultiregimpl50 <= request;
	xilinxmultiregimpl51 <= xilinxmultiregimpl50;
	xilinxmultiregimpl60 <= abandoned;
	xilinxmultiregimpl61 <= xilinxmultiregimpl60;
end

always @(posedge management_clk) begin
	xilinxmultiregimpl70 <= coordinator_reset;
	xilinxmultiregimpl71 <= xilinxmultiregimpl70;
	xilinxmultiregimpl80 <= registered_abandonment_ready;
	xilinxmultiregimpl81 <= xilinxmultiregimpl80;
	xilinxmultiregimpl90 <= registered_admit;
	xilinxmultiregimpl91 <= xilinxmultiregimpl90;
end

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE (
	.C(aux_release_ps_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(releases_request),
	.Q(rst_meta0)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_1 (
	.C(aux_release_ps_clk),
	.CE(1'd1),
	.D(rst_meta0),
	.PRE(releases_request),
	.Q(aux_release_ps_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_2 (
	.C(aux_release_sys_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(releases_request),
	.Q(rst_meta1)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_3 (
	.C(aux_release_sys_clk),
	.CE(1'd1),
	.D(rst_meta1),
	.PRE(releases_request),
	.Q(aux_release_sys_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_4 (
	.C(aux_release_rtio_rx_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(releases_request),
	.Q(rst_meta2)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_5 (
	.C(aux_release_rtio_rx_clk),
	.CE(1'd1),
	.D(rst_meta2),
	.PRE(releases_request),
	.Q(aux_release_rtio_rx_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_6 (
	.C(aux_release_rio_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(releases_request),
	.Q(rst_meta3)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_7 (
	.C(aux_release_rio_clk),
	.CE(1'd1),
	.D(rst_meta3),
	.PRE(releases_request),
	.Q(aux_release_rio_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_8 (
	.C(aux_release_rio_phy_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(releases_request),
	.Q(rst_meta4)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_9 (
	.C(aux_release_rio_phy_clk),
	.CE(1'd1),
	.D(rst_meta4),
	.PRE(releases_request),
	.Q(aux_release_rio_phy_rst)
);

endmodule
