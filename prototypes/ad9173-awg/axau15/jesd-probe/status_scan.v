module status_scan(input [8:0] status);
wire tck,capture,shift,sel;
(* ASYNC_REG="TRUE" *) reg [8:0] meta=0,sync_status=0;
reg [63:0] scan=0;
always @(posedge tck) begin
 meta<=status;sync_status<=meta;
 if(sel) begin
  if(capture) scan<={32'h41584a31,23'b0,sync_status};
  else if(shift) scan<={1'b0,scan[63:1]};
 end
end
BSCANE2 #(.JTAG_CHAIN(1)) bs(.TCK(tck),.CAPTURE(capture),.SHIFT(shift),.SEL(sel),.TDO(scan[0]));
endmodule
