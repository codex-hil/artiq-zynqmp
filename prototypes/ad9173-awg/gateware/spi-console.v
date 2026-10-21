`timescale 1ns/1ps
// USER2 stable-mailbox command transport; no flash/OTP access or automatic resets.
module spi_console(input clk,input spi_en,input miso,output reg sck=0,mosi=0,output reg cs_dac=1,cs_clock=1,output reg [15:0] payload_amp=16'h2000);
wire capture,shift,update,tck,sel,tdi;
reg [127:0] scan=0;
reg [31:0] mailbox_cmd=0;reg [15:0] mailbox_seq=0;reg request=0;
reg [15:0] done_seq=0;reg [31:0] echo=0;reg [7:0] result=0;reg busy=0,error=0;
wire [31:0] flags={21'b0,error,spi_en,busy,result};
BSCANE2 #(.JTAG_CHAIN(2)) bs(.CAPTURE(capture),.DRCK(),.RESET(),.RUNTEST(),.SEL(sel),.SHIFT(shift),.TCK(tck),.TDI(tdi),.TMS(),.UPDATE(update),.TDO(scan[0]));
always @(posedge tck) if(sel) begin
 if(capture)scan<={32'h53504952,echo,16'b0,done_seq,flags};
 else if(shift)scan<={tdi,scan[127:1]};
 if(update && scan[127:96]==32'h53504943 && scan[47:32]!=mailbox_seq) begin mailbox_cmd<=scan[31:0];mailbox_seq<=scan[47:32];request<=~request;end
end
(* ASYNC_REG="TRUE" *) reg [1:0] req_sync=0;
reg seen=0;reg [7:0] divider=0;reg [1:0] state=0;reg [4:0] bit_index=23;reg [23:0] command=0;reg [15:0] active_seq=0;reg [7:0] rx=0;reg target=0;
always @(posedge clk) begin
 req_sync<={req_sync[0],request};divider<=divider+1'b1;
 if(req_sync[1]!=seen) begin
  seen<=req_sync[1];echo<=mailbox_cmd;
  if(mailbox_cmd[25] && !busy) begin payload_amp<=mailbox_cmd[15:0];result<=mailbox_cmd[7:0];done_seq<=mailbox_seq;error<=0;end
  else if(spi_en || busy) begin error<=1;done_seq<=mailbox_seq;end
  else begin command<=mailbox_cmd[23:0];target<=mailbox_cmd[24];active_seq<=mailbox_seq;bit_index<=23;rx<=0;error<=0;busy<=1;state<=1;end
 end
 if(spi_en && busy) begin cs_dac<=1;cs_clock<=1;sck<=0;busy<=0;state<=0;error<=1;done_seq<=active_seq;end
 else if(divider==0 && busy) case(state)
 1:begin cs_dac<=target;cs_clock<=~target;mosi<=command[23];sck<=0;state<=2;end
 2:begin sck<=1;if(bit_index<8)rx<={rx[6:0],miso};state<=3;end
 3:begin
  sck<=0;
  if(bit_index==0)begin cs_dac<=1;cs_clock<=1;result<=rx;busy<=0;state<=0;done_seq<=active_seq;end
  else begin bit_index<=bit_index-1'b1;command<={command[22:0],1'b0};mosi<=command[22];state<=2;end
 end
 endcase
end
endmodule
