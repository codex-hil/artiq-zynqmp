`timescale 1ns/1ps
// Single TCK domain, host-paced GPIO. No autonomous SPI or arbitrary register writes.
module spi_probe_core(input tck,capture,shift,update,sel,tdi,input miso,spi_en,
 output tdo,output reg [3:0] pins=4'b1100,output owner);
reg [63:0] scan=0;
(* ASYNC_REG="TRUE" *) reg [1:0] miso_sync=0;
(* ASYNC_REG="TRUE" *) reg [1:0] owner_sync=3;
assign tdo=scan[0]; assign owner=owner_sync[1];
always @(posedge tck) begin
 miso_sync<={miso_sync[0],miso};owner_sync<={owner_sync[0],spi_en};
 if(owner_sync[1]) pins<=4'b1100;
 if(sel) begin
  if(capture) scan<={32'h41534762,26'b0,owner_sync[1],miso_sync[1],pins};
  else if(shift) scan<={tdi,scan[63:1]};
  if(update && scan[63:32]==32'h41534760 && !owner_sync[1]) pins<= (|scan[3:2]) ? scan[3:0] : 4'b1100;
 end
end
endmodule
