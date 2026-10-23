module clock_probe(input sys_p, sys_n);
wire raw,clk;
IBUFDS ib(.I(sys_p),.IB(sys_n),.O(raw));
BUFGCE_DIV #(.BUFGCE_DIVIDE(2)) bu(.I(raw),.CE(1'b1),.CLR(1'b0),.O(clk));
reg [31:0] count=0,gray=0;
wire [31:0] next_count=count+1;
always @(posedge clk) begin count<=next_count;gray<=next_count^(next_count>>1);end
wire tck,capture,shift,sel;
reg [63:0] scan=0;
(* ASYNC_REG="TRUE" *) reg [31:0] meta=0,sync_gray=0;
always @(posedge tck) begin
 meta<=gray;sync_gray<=meta;
 if(sel) begin
  if(capture) scan<={32'h41583135,sync_gray};
  else if(shift) scan<={1'b0,scan[63:1]};
 end
end
BSCANE2 #(.JTAG_CHAIN(1)) bs(.TCK(tck),.CAPTURE(capture),.SHIFT(shift),.SEL(sel),.TDO(scan[0]));
endmodule
