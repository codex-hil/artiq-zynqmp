module eth_scan(input [3:0] status,input mdi, output reg [3:0] pins=0);
wire tck,capture,shift,update,sel,tdi;
(* ASYNC_REG="TRUE" *) reg [4:0] meta=0,sync_bits=0;
reg [63:0] scan=0;
always @(posedge tck) begin
 meta<={mdi,status};sync_bits<=meta;
 if(sel) begin
  if(capture) scan<={32'h41584562,23'b0,sync_bits,pins};
  else if(shift) scan<={tdi,scan[63:1]};
  if(update && scan[63:32]==32'h41584560) pins<=scan[3:0];
 end
end
BSCANE2 #(.JTAG_CHAIN(3)) bs(.TCK(tck),.CAPTURE(capture),.SHIFT(shift),.UPDATE(update),.SEL(sel),.TDI(tdi),.TDO(scan[0]));
endmodule
