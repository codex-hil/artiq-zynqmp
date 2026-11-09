`timescale 1ns/1ps
/* Machine-generated using Migen */
module reset_coordinator(
	input management_clock,
	input control_clock,
	input a_clock,
	input b_clock,
	output coordinator_reset,
	output reg [1:0] domain_ready,
	output reg [1:0] target_reset,
	input request,
	input abandoned,
	output reset_status,
	output abandon_ready,
	output admit
);

wire management_clk;
wire control_clk;
reg control_rst = 1'd0;
wire a_clk;
wire a_rst;
wire b_clk;
wire b_rst;
wire request_1;
wire [1:0] domain_ready_1;
wire requester_abandoned;
wire admit_1;
wire abandonment_ready;
reg low_seen = 1'd0;
reg abandonment_seen = 1'd0;
reg is_ongoing0;
reg is_ongoing1;
reg is_ongoing2;
reg is_ongoing3;
wire releases_request;
wire aux_release_a_clk;
wire aux_release_a_rst;
reg [1:0] releases_count0 = 2'd0;
reg releases_local_ready0 = 1'd0;
wire aux_release_b_clk;
wire aux_release_b_rst;
reg [1:0] releases_count1 = 2'd0;
reg releases_local_ready1 = 1'd0;
reg [1:0] state = 2'd0;
reg [1:0] next_state;
wire rst_meta0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl00 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl01 = 1'd0;
wire rst_meta1;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl10 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl11 = 1'd0;
(* async_reg = "true", mr_ff = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl20 = 1'd0;
(* async_reg = "true", no_retiming = "true", no_shreg_extract = "true" *) reg xilinxmultiregimpl21 = 1'd0;
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

assign management_clk = management_clock;
assign control_clk = control_clock;
assign a_clk = a_clock;
assign b_clk = b_clock;
assign releases_request = coordinator_reset;
assign domain_ready_1 = domain_ready;
assign a_rst = target_reset[0];
assign b_rst = target_reset[1];
assign abandonment_ready = (((is_ongoing0 & (~request_1)) & low_seen) & (~abandonment_seen));
assign coordinator_reset = (is_ongoing1 | request_1);
assign admit_1 = ((is_ongoing2 & (~request_1)) & (domain_ready_1 == 2'd3));

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
				if ((domain_ready_1 == 2'd3)) begin
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
assign aux_release_a_clk = a_clk;
assign aux_release_b_clk = b_clk;

// synthesis translate_off
reg dummy_d_1;
// synthesis translate_on
always @(*) begin
	target_reset <= 2'd0;
	target_reset[0] <= aux_release_a_rst;
	target_reset[1] <= aux_release_b_rst;
// synthesis translate_off
	dummy_d_1 <= dummy_s;
// synthesis translate_on
end

// synthesis translate_off
reg dummy_d_2;
// synthesis translate_on
always @(*) begin
	domain_ready <= 2'd0;
	domain_ready[0] <= xilinxmultiregimpl01;
	domain_ready[1] <= xilinxmultiregimpl11;
// synthesis translate_off
	dummy_d_2 <= dummy_s;
// synthesis translate_on
end
assign request_1 = xilinxmultiregimpl21;
assign requester_abandoned = xilinxmultiregimpl31;
assign reset_status = xilinxmultiregimpl41;
assign abandon_ready = xilinxmultiregimpl51;
assign admit = xilinxmultiregimpl61;

always @(posedge aux_release_a_clk) begin
	if ((releases_count0 != 2'd3)) begin
		releases_count0 <= (releases_count0 + 1'd1);
	end else begin
		releases_local_ready0 <= 1'd1;
	end
	if (aux_release_a_rst) begin
		releases_count0 <= 2'd0;
		releases_local_ready0 <= 1'd0;
	end
end

always @(posedge aux_release_b_clk) begin
	if ((releases_count1 != 2'd3)) begin
		releases_count1 <= (releases_count1 + 1'd1);
	end else begin
		releases_local_ready1 <= 1'd1;
	end
	if (aux_release_b_rst) begin
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
	if (control_rst) begin
		low_seen <= 1'd0;
		abandonment_seen <= 1'd0;
		state <= 2'd0;
	end
	xilinxmultiregimpl00 <= releases_local_ready0;
	xilinxmultiregimpl01 <= xilinxmultiregimpl00;
	xilinxmultiregimpl10 <= releases_local_ready1;
	xilinxmultiregimpl11 <= xilinxmultiregimpl10;
	xilinxmultiregimpl20 <= request;
	xilinxmultiregimpl21 <= xilinxmultiregimpl20;
	xilinxmultiregimpl30 <= abandoned;
	xilinxmultiregimpl31 <= xilinxmultiregimpl30;
end

always @(posedge management_clk) begin
	xilinxmultiregimpl40 <= coordinator_reset;
	xilinxmultiregimpl41 <= xilinxmultiregimpl40;
	xilinxmultiregimpl50 <= abandonment_ready;
	xilinxmultiregimpl51 <= xilinxmultiregimpl50;
	xilinxmultiregimpl60 <= admit_1;
	xilinxmultiregimpl61 <= xilinxmultiregimpl60;
end

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE (
	.C(aux_release_a_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(releases_request),
	.Q(rst_meta0)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_1 (
	.C(aux_release_a_clk),
	.CE(1'd1),
	.D(rst_meta0),
	.PRE(releases_request),
	.Q(aux_release_a_rst)
);

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_2 (
	.C(aux_release_b_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(releases_request),
	.Q(rst_meta1)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_3 (
	.C(aux_release_b_clk),
	.CE(1'd1),
	.D(rst_meta1),
	.PRE(releases_request),
	.Q(aux_release_b_rst)
);

endmodule
