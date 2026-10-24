-- Flat-language boundary around the unmodified upstream IPbus v1.16 controller.
library ieee;
use ieee.std_logic_1164.all;
use work.ipbus.all;
use work.ipbus_trans_decl.all;
entity rng_ipbus_endpoint is
port(
 mac_clk,rst_macclk,ipb_clk,rst_ipb: in std_logic;
 mac_rx_data: in std_logic_vector(7 downto 0);
 mac_rx_valid,mac_rx_last,mac_rx_error: in std_logic;
 mac_tx_data: out std_logic_vector(7 downto 0);
 mac_tx_valid,mac_tx_last,mac_tx_error: out std_logic;
 mac_tx_ready: in std_logic;
 mac_addr: in std_logic_vector(47 downto 0);
 ip_addr: in std_logic_vector(31 downto 0);
 ipb_addr,ipb_wdata: out std_logic_vector(31 downto 0);
 ipb_strobe,ipb_write: out std_logic;
 ipb_rdata: in std_logic_vector(31 downto 0);
 ipb_ack,ipb_err: in std_logic;
 got_ip:out std_logic
);
end entity;
architecture rtl of rng_ipbus_endpoint is
 signal wb:ipb_wbus;signal rb:ipb_rbus;
begin
 ipb_addr<=wb.ipb_addr;ipb_wdata<=wb.ipb_wdata;
 ipb_strobe<=wb.ipb_strobe;ipb_write<=wb.ipb_write;
 rb.ipb_rdata<=ipb_rdata;rb.ipb_ack<=ipb_ack;rb.ipb_err<=ipb_err;
 controller:entity work.ipbus_ctrl
 generic map(BUFWIDTH=>4,INTERNALWIDTH=>1,ADDRWIDTH=>11,N_OOB=>0)
 port map(mac_clk=>mac_clk,rst_macclk=>rst_macclk,ipb_clk=>ipb_clk,rst_ipb=>rst_ipb,
 mac_rx_data=>mac_rx_data,mac_rx_valid=>mac_rx_valid,mac_rx_last=>mac_rx_last,mac_rx_error=>mac_rx_error,
 mac_tx_data=>mac_tx_data,mac_tx_valid=>mac_tx_valid,mac_tx_last=>mac_tx_last,mac_tx_error=>mac_tx_error,mac_tx_ready=>mac_tx_ready,
 ipb_out=>wb,ipb_in=>rb,ipb_req=>open,ipb_grant=>'1',mac_addr=>mac_addr,ip_addr=>ip_addr,
 enable=>'1',ipam_select=>'0',actual_mac_addr=>open,actual_ip_addr=>open,Got_IP_addr=>got_ip,pkt=>open,pkt_oob=>open,oob_out=>open);
end architecture;
