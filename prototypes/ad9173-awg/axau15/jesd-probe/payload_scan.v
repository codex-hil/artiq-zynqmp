// Volatile lab payload mailbox. Source holds data until destination acknowledgement.
// No PRBS/data-bit overloading. FPGA configuration initializes amplitude to zero.
module payload_core(input tck,capture,shift,update,sel,tdi,clk,
 output tdo,output reg [15:0] amplitude=0);
reg [63:0] scan=0;
reg [15:0] held=0;
reg request=0, acknowledge=0;
(* ASYNC_REG="TRUE" *) reg [1:0] req_sync=0,ack_sync=0;
wire busy=request!=ack_sync[1];
assign tdo=scan[0];
always @(posedge tck) begin
 ack_sync<={ack_sync[0],acknowledge};
 if(sel) begin
  if(capture) scan<={32'h41585062,15'b0,busy,held};
  else if(shift) scan<={tdi,scan[63:1]};
  if(update && scan[63:32]==32'h41585060 && !busy) begin
   held<=scan[15:0];request<=~request;
  end
 end
end
always @(posedge clk) begin
 req_sync<={req_sync[0],request};
 if(req_sync[1]!=acknowledge) begin
  amplitude<=held;
  acknowledge<=req_sync[1];
 end
end
endmodule
module payload_scan(input clk,output [15:0] amplitude);
wire tck,capture,shift,update,sel,tdi,tdo;
BSCANE2 #(.JTAG_CHAIN(3)) bs(.TCK(tck),.CAPTURE(capture),.SHIFT(shift),.UPDATE(update),.SEL(sel),.TDI(tdi),.TDO(tdo));
payload_core core(.tck(tck),.capture(capture),.shift(shift),.update(update),.sel(sel),.tdi(tdi),.tdo(tdo),.clk(clk),.amplitude(amplitude));
endmodule
