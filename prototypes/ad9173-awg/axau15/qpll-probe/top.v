`timescale 1ns/1ps
module spi_probe(input sys_p,sys_n,input ref_p,ref_n,input miso,spi_en,output sck,mosi,cs_dac,cs_clock);
wire tck,capture,shift,update,sel,tdi,tdo,owner;
wire [3:0] pins;
BSCANE2 #(.JTAG_CHAIN(2)) bs(.TCK(tck),.CAPTURE(capture),.SHIFT(shift),.UPDATE(update),.SEL(sel),.TDI(tdi),.TDO(tdo));
spi_probe_core core(.tck(tck),.capture(capture),.shift(shift),.update(update),.sel(sel),.tdi(tdi),.tdo(tdo),.miso(miso),.spi_en(spi_en),.pins(pins),.owner(owner));
// PIC owns SPI_EN. Immediate high-Z on ownership handoff, no FPGA drive of SPI_EN.
assign sck=spi_en ? 1'bz:pins[0];
assign mosi=spi_en ? 1'bz:pins[1];
assign cs_dac=spi_en ? 1'bz:pins[2];
assign cs_clock=spi_en ? 1'bz:pins[3];
// Dedicated FMC reference receiver; ODIV2 is explicitly divide-by-two.
wire ref_raw,ref_div,ref_clk;
IBUFDS_GTE4 #(.REFCLK_HROW_CK_SEL(2'b01)) ref_ib
 (.I(ref_p),.IB(ref_n),.CEB(1'b0),.O(ref_raw),.ODIV2(ref_div));
BUFG_GT ref_buf (.I(ref_div),.CE(1'b1),.CEMASK(1'b0),.CLR(1'b0),.CLRMASK(1'b0),.DIV(3'b000),.O(ref_clk));
wire sys_raw,sys_clk,qpll_locked;
IBUFDS sys_ib (.I(sys_p),.IB(sys_n),.O(sys_raw));
BUFGCE_DIV #(.BUFGCE_DIVIDE(2)) sys_buf (.I(sys_raw),.CE(1'b1),.CLR(1'b0),.O(sys_clk));
// Hold reset for 1024 independent system-clock cycles after configuration.
reg [10:0] startup=0;
always @(posedge sys_clk) if(!startup[10]) startup<=startup+1'b1;
qpll_common common (.sys_clk(sys_clk),.refclk(ref_raw),.reset(!startup[10]),.locked(qpll_locked));
(* ASYNC_REG="TRUE" *) reg [1:0] lock_sync=0;
reg [31:0] count=0,gray=0;
wire [31:0] next_count=count+1;
always @(posedge ref_clk) begin count<=next_count;gray<=next_count^(next_count>>1);end
wire probe_tck,probe_capture,probe_shift,probe_sel;
reg [63:0] scan=0;
(* ASYNC_REG="TRUE" *) reg [31:0] meta=0,sync_gray=0;
always @(posedge probe_tck) begin
 meta<=gray;sync_gray<=meta;lock_sync<={lock_sync[0],qpll_locked};
 if(probe_sel) begin
  if(probe_capture) scan<={31'h20ac2898,lock_sync[1],sync_gray};
  else if(probe_shift) scan<={1'b0,scan[63:1]};
 end
end
BSCANE2 #(.JTAG_CHAIN(1)) probe_bs(.TCK(probe_tck),.CAPTURE(probe_capture),.SHIFT(probe_shift),.SEL(probe_sel),.TDO(scan[0]));
endmodule
