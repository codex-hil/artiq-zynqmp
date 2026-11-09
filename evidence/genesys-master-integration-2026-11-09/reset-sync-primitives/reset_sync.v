`timescale 1ns/1ps
/* Machine-generated using Migen */
module reset_sync(
	output reset_out,
	input source_clk,
	input reset_request
);

wire rx_clk;
wire rst_meta;

// synthesis translate_off
reg dummy_s;
initial dummy_s <= 1'd0;
// synthesis translate_on

assign rx_clk = source_clk;

(* ars_ff1 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE (
	.C(rx_clk),
	.CE(1'd1),
	.D(1'd0),
	.PRE(reset_request),
	.Q(rst_meta)
);

(* ars_ff2 = "true", async_reg = "true" *) FDPE #(
	.INIT(1'd1)
) FDPE_1 (
	.C(rx_clk),
	.CE(1'd1),
	.D(rst_meta),
	.PRE(reset_request),
	.Q(reset_out)
);

endmodule
