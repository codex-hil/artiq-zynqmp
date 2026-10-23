`timescale 1ns/1ps
module tb;
reg tck=0,capture=0,shift=0,update=0,sel=1,tdi=0,miso=0,spi_en=0;
wire tdo,owner;wire [3:0] pins;
spi_probe_core dut(.*);
always #50 tck=~tck;
reg [63:0] rx;
task scan(input [63:0] value);
 integer i;begin
 @(negedge tck);capture=1;@(negedge tck);capture=0;shift=1;
 for(i=0;i<64;i=i+1)begin tdi=value[i];rx[i]=tdo;@(negedge tck);end
 shift=0;update=1;@(negedge tck);update=0;
 end
endtask
initial begin
 repeat(4)@(negedge tck);
 scan(64'h415347600000000a);
 if(pins!==4'b1010)$fatal(1,"valid update failed");
 scan(64'hdeadbeef0000000f);
 if(pins!==4'b1010)$fatal(1,"bad magic mutated outputs");
 if(rx[63:32]!==32'h41534762)$fatal(1,"bad signature");
 miso=1; repeat(4)@(negedge tck);scan(0);
 if(rx[4]!==1)$fatal(1,"MISO capture failed");
 spi_en=1;repeat(4)@(negedge tck);scan(64'h415347600000000b);
 if(pins!==4'b1100 || rx[5]!==1)$fatal(1,"ownership guard failed");
 spi_en=0;repeat(4)@(negedge tck);scan(64'h4153476000000009);
 if(pins!==4'b1001)$fatal(1,"ownership recovery failed");
 scan(64'h4153476000000000);
 if(pins!==4'b1100)$fatal(1,"both chip selects allowed");
 scan(64'h4153476000000004);
 if(pins!==4'b0100)$fatal(1,"HMC selection failed");
 $display("DUAL_SPI_CORE_SIMULATION_PASS");$finish;
end
initial begin #1000000;$fatal(1,"timeout");end
endmodule
