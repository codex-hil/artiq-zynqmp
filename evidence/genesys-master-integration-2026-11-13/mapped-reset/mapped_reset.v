`timescale 1ns/1ps
module mapped_reset #(parameter MUTATE_CE=0,MUTATE_AND=0)(input pl_clock,tx_clock,pl_resetn,raw_reset,output control_reset,coordinator_reset,retained_request,sys_reset);
wire n0,n1,n2,n3,n4,n5,n6,n7,n8;
LUT2 #(.INIT(MUTATE_AND ? 4'h8 : 4'hE)) cell0(.O(n5),.I0(n4),.I1(n3));
FDPE #(.INIT(1'b1),.IS_C_INVERTED(1'b0),.IS_D_INVERTED(1'b0),.IS_PRE_INVERTED(1'b0)) cell1(.Q(n6),.C(tx_clock),.CE(n1),.D(n0),.PRE(n5));
FDPE #(.INIT(1'b1),.IS_C_INVERTED(1'b0),.IS_D_INVERTED(1'b0),.IS_PRE_INVERTED(1'b0)) cell2(.Q(n2),.C(tx_clock),.CE(n1),.D(n6),.PRE(n5));
LUT1 #(.INIT(2'h1)) cell3(.O(n7),.I0(pl_resetn));
FDPE #(.INIT(1'b1),.IS_C_INVERTED(1'b0),.IS_D_INVERTED(1'b0),.IS_PRE_INVERTED(1'b0)) cell4(.Q(n8),.C(pl_clock),.CE(n1),.D(n0),.PRE(n7));
FDPE #(.INIT(1'b1),.IS_C_INVERTED(1'b0),.IS_D_INVERTED(1'b0),.IS_PRE_INVERTED(1'b0)) cell5(.Q(n3),.C(pl_clock),.CE(n1),.D(n8),.PRE(n7));
GND cell6(.G(n0));
VCC cell7(.P(n1));
FDSE #(.INIT(1'b1)) cell8(.Q(n4),.C(pl_clock),.CE(MUTATE_CE ? 1'b0 : n1),.D(raw_reset),.S(n3));
assign control_reset=n3;
assign coordinator_reset=n4;
assign sys_reset=n2;
assign retained_request=n5;
endmodule
