`timescale 1ns/1ps
module spi_probe(input miso,spi_en,output sck,mosi,cs_dac,cs_clock);
wire tck,capture,shift,update,sel,tdi,tdo,owner;
wire [3:0] pins;
BSCANE2 #(.JTAG_CHAIN(2)) bs(.TCK(tck),.CAPTURE(capture),.SHIFT(shift),.UPDATE(update),.SEL(sel),.TDI(tdi),.TDO(tdo));
spi_probe_core core(.tck(tck),.capture(capture),.shift(shift),.update(update),.sel(sel),.tdi(tdi),.tdo(tdo),.miso(miso),.spi_en(spi_en),.pins(pins),.owner(owner));
// PIC owns SPI_EN. Immediate high-Z on ownership handoff, no FPGA drive of SPI_EN.
assign sck=spi_en ? 1'bz:pins[0];
assign mosi=spi_en ? 1'bz:pins[1];
assign cs_dac=spi_en ? 1'bz:pins[2];
assign cs_clock=spi_en ? 1'bz:pins[3];
endmodule
