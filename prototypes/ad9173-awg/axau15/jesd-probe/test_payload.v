`timescale 1ns/1ps
module test_payload;
reg tck=0,clk=0,runclk=1,capture=0,shift=0,update=0,sel=1,tdi=0;
wire tdo;wire [15:0] amplitude;
payload_core dut(tck,capture,shift,update,sel,tdi,clk,tdo,amplitude);
always #7 tck=~tck;
always #3.25 if(runclk) clk=~clk;
task send(input [63:0] value);
 integer i;
 begin
  for(i=0;i<64;i=i+1) begin
   @(negedge tck);shift=1;tdi=value[i];
  end
  @(negedge tck);shift=0;update=1;
  @(negedge tck);update=0;
 end
endtask
task expect_amp(input [15:0] value);
 begin
  #200;
  if(amplitude!==value || dut.busy!==0) $fatal(1,"amplitude or ack mismatch %x expected %x",amplitude,value);
 end
endtask
initial begin
 #100;expect_amp(0);
 send(64'h0000000000007fff);expect_amp(0);
 send(64'h4158506000007fff);expect_amp(16'h7fff);
 send(64'h4158506000004000);expect_amp(16'h4000);
 send(64'h4158506000000000);expect_amp(0);
 send(64'h4158506000005a82);expect_amp(16'h5a82);
 send(64'h4158506000008001);expect_amp(16'h8001);
 // Stopped JESD clock: source must stay busy, reject a second update,
 // then deliver the first complete word when destination resumes.
 @(negedge clk);runclk=0;
 send(64'h4158506000001234);
 if(!dut.busy) $fatal(1,"missing busy on stopped destination");
 send(64'h4158506000007654);
 if(dut.held!==16'h1234 || amplitude!==16'h8001) $fatal(1,"busy overwrite/torn word");
 runclk=1;expect_amp(16'h1234);
 send(64'h4158506000007fff);expect_amp(16'h7fff);
 $display("PASS payload: zero init, magic, full/half/zero/recovery, asymmetric/signed, paused clock, busy reject");
 $finish;
end
initial begin #100000;$fatal(1,"timeout");end
endmodule
