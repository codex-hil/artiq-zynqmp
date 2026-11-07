//Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
//Copyright 2022-2025 Advanced Micro Devices, Inc. All Rights Reserved.
//--------------------------------------------------------------------------------
//Tool Version: Vivado v.2025.2 (lin64) Build 6299465 Fri Nov 14 12:34:56 MST 2025
//Date        : Sat Nov  7 18:54:24 2026
//Host        : codex-hil-Precision-5820-Tower-X-Series running 64-bit Ubuntu 22.04.5 LTS
//Command     : generate_target dual_hpm_wrapper.bd
//Design      : dual_hpm_wrapper
//Purpose     : IP block netlist
//--------------------------------------------------------------------------------
`timescale 1 ps / 1 ps

module dual_hpm_wrapper
   (M_AXI_HPM0_FPD_0_araddr,
    M_AXI_HPM0_FPD_0_arburst,
    M_AXI_HPM0_FPD_0_arcache,
    M_AXI_HPM0_FPD_0_arid,
    M_AXI_HPM0_FPD_0_arlen,
    M_AXI_HPM0_FPD_0_arlock,
    M_AXI_HPM0_FPD_0_arprot,
    M_AXI_HPM0_FPD_0_arqos,
    M_AXI_HPM0_FPD_0_arready,
    M_AXI_HPM0_FPD_0_arsize,
    M_AXI_HPM0_FPD_0_aruser,
    M_AXI_HPM0_FPD_0_arvalid,
    M_AXI_HPM0_FPD_0_awaddr,
    M_AXI_HPM0_FPD_0_awburst,
    M_AXI_HPM0_FPD_0_awcache,
    M_AXI_HPM0_FPD_0_awid,
    M_AXI_HPM0_FPD_0_awlen,
    M_AXI_HPM0_FPD_0_awlock,
    M_AXI_HPM0_FPD_0_awprot,
    M_AXI_HPM0_FPD_0_awqos,
    M_AXI_HPM0_FPD_0_awready,
    M_AXI_HPM0_FPD_0_awsize,
    M_AXI_HPM0_FPD_0_awuser,
    M_AXI_HPM0_FPD_0_awvalid,
    M_AXI_HPM0_FPD_0_bid,
    M_AXI_HPM0_FPD_0_bready,
    M_AXI_HPM0_FPD_0_bresp,
    M_AXI_HPM0_FPD_0_bvalid,
    M_AXI_HPM0_FPD_0_rdata,
    M_AXI_HPM0_FPD_0_rid,
    M_AXI_HPM0_FPD_0_rlast,
    M_AXI_HPM0_FPD_0_rready,
    M_AXI_HPM0_FPD_0_rresp,
    M_AXI_HPM0_FPD_0_rvalid,
    M_AXI_HPM0_FPD_0_wdata,
    M_AXI_HPM0_FPD_0_wlast,
    M_AXI_HPM0_FPD_0_wready,
    M_AXI_HPM0_FPD_0_wstrb,
    M_AXI_HPM0_FPD_0_wvalid,
    M_AXI_HPM1_FPD_0_araddr,
    M_AXI_HPM1_FPD_0_arburst,
    M_AXI_HPM1_FPD_0_arcache,
    M_AXI_HPM1_FPD_0_arid,
    M_AXI_HPM1_FPD_0_arlen,
    M_AXI_HPM1_FPD_0_arlock,
    M_AXI_HPM1_FPD_0_arprot,
    M_AXI_HPM1_FPD_0_arqos,
    M_AXI_HPM1_FPD_0_arready,
    M_AXI_HPM1_FPD_0_arsize,
    M_AXI_HPM1_FPD_0_aruser,
    M_AXI_HPM1_FPD_0_arvalid,
    M_AXI_HPM1_FPD_0_awaddr,
    M_AXI_HPM1_FPD_0_awburst,
    M_AXI_HPM1_FPD_0_awcache,
    M_AXI_HPM1_FPD_0_awid,
    M_AXI_HPM1_FPD_0_awlen,
    M_AXI_HPM1_FPD_0_awlock,
    M_AXI_HPM1_FPD_0_awprot,
    M_AXI_HPM1_FPD_0_awqos,
    M_AXI_HPM1_FPD_0_awready,
    M_AXI_HPM1_FPD_0_awsize,
    M_AXI_HPM1_FPD_0_awuser,
    M_AXI_HPM1_FPD_0_awvalid,
    M_AXI_HPM1_FPD_0_bid,
    M_AXI_HPM1_FPD_0_bready,
    M_AXI_HPM1_FPD_0_bresp,
    M_AXI_HPM1_FPD_0_bvalid,
    M_AXI_HPM1_FPD_0_rdata,
    M_AXI_HPM1_FPD_0_rid,
    M_AXI_HPM1_FPD_0_rlast,
    M_AXI_HPM1_FPD_0_rready,
    M_AXI_HPM1_FPD_0_rresp,
    M_AXI_HPM1_FPD_0_rvalid,
    M_AXI_HPM1_FPD_0_wdata,
    M_AXI_HPM1_FPD_0_wlast,
    M_AXI_HPM1_FPD_0_wready,
    M_AXI_HPM1_FPD_0_wstrb,
    M_AXI_HPM1_FPD_0_wvalid,
    emio_enet0_enet_tsu_timer_cnt_0,
    maxihpm0_fpd_aclk_0,
    maxihpm1_fpd_aclk_0,
    pl_clk0_0,
    pl_ps_irq0_0,
    pl_resetn0_0);
  output [39:0]M_AXI_HPM0_FPD_0_araddr;
  output [1:0]M_AXI_HPM0_FPD_0_arburst;
  output [3:0]M_AXI_HPM0_FPD_0_arcache;
  output [15:0]M_AXI_HPM0_FPD_0_arid;
  output [7:0]M_AXI_HPM0_FPD_0_arlen;
  output M_AXI_HPM0_FPD_0_arlock;
  output [2:0]M_AXI_HPM0_FPD_0_arprot;
  output [3:0]M_AXI_HPM0_FPD_0_arqos;
  input M_AXI_HPM0_FPD_0_arready;
  output [2:0]M_AXI_HPM0_FPD_0_arsize;
  output [15:0]M_AXI_HPM0_FPD_0_aruser;
  output M_AXI_HPM0_FPD_0_arvalid;
  output [39:0]M_AXI_HPM0_FPD_0_awaddr;
  output [1:0]M_AXI_HPM0_FPD_0_awburst;
  output [3:0]M_AXI_HPM0_FPD_0_awcache;
  output [15:0]M_AXI_HPM0_FPD_0_awid;
  output [7:0]M_AXI_HPM0_FPD_0_awlen;
  output M_AXI_HPM0_FPD_0_awlock;
  output [2:0]M_AXI_HPM0_FPD_0_awprot;
  output [3:0]M_AXI_HPM0_FPD_0_awqos;
  input M_AXI_HPM0_FPD_0_awready;
  output [2:0]M_AXI_HPM0_FPD_0_awsize;
  output [15:0]M_AXI_HPM0_FPD_0_awuser;
  output M_AXI_HPM0_FPD_0_awvalid;
  input [15:0]M_AXI_HPM0_FPD_0_bid;
  output M_AXI_HPM0_FPD_0_bready;
  input [1:0]M_AXI_HPM0_FPD_0_bresp;
  input M_AXI_HPM0_FPD_0_bvalid;
  input [31:0]M_AXI_HPM0_FPD_0_rdata;
  input [15:0]M_AXI_HPM0_FPD_0_rid;
  input M_AXI_HPM0_FPD_0_rlast;
  output M_AXI_HPM0_FPD_0_rready;
  input [1:0]M_AXI_HPM0_FPD_0_rresp;
  input M_AXI_HPM0_FPD_0_rvalid;
  output [31:0]M_AXI_HPM0_FPD_0_wdata;
  output M_AXI_HPM0_FPD_0_wlast;
  input M_AXI_HPM0_FPD_0_wready;
  output [3:0]M_AXI_HPM0_FPD_0_wstrb;
  output M_AXI_HPM0_FPD_0_wvalid;
  output [39:0]M_AXI_HPM1_FPD_0_araddr;
  output [1:0]M_AXI_HPM1_FPD_0_arburst;
  output [3:0]M_AXI_HPM1_FPD_0_arcache;
  output [15:0]M_AXI_HPM1_FPD_0_arid;
  output [7:0]M_AXI_HPM1_FPD_0_arlen;
  output M_AXI_HPM1_FPD_0_arlock;
  output [2:0]M_AXI_HPM1_FPD_0_arprot;
  output [3:0]M_AXI_HPM1_FPD_0_arqos;
  input M_AXI_HPM1_FPD_0_arready;
  output [2:0]M_AXI_HPM1_FPD_0_arsize;
  output [15:0]M_AXI_HPM1_FPD_0_aruser;
  output M_AXI_HPM1_FPD_0_arvalid;
  output [39:0]M_AXI_HPM1_FPD_0_awaddr;
  output [1:0]M_AXI_HPM1_FPD_0_awburst;
  output [3:0]M_AXI_HPM1_FPD_0_awcache;
  output [15:0]M_AXI_HPM1_FPD_0_awid;
  output [7:0]M_AXI_HPM1_FPD_0_awlen;
  output M_AXI_HPM1_FPD_0_awlock;
  output [2:0]M_AXI_HPM1_FPD_0_awprot;
  output [3:0]M_AXI_HPM1_FPD_0_awqos;
  input M_AXI_HPM1_FPD_0_awready;
  output [2:0]M_AXI_HPM1_FPD_0_awsize;
  output [15:0]M_AXI_HPM1_FPD_0_awuser;
  output M_AXI_HPM1_FPD_0_awvalid;
  input [15:0]M_AXI_HPM1_FPD_0_bid;
  output M_AXI_HPM1_FPD_0_bready;
  input [1:0]M_AXI_HPM1_FPD_0_bresp;
  input M_AXI_HPM1_FPD_0_bvalid;
  input [31:0]M_AXI_HPM1_FPD_0_rdata;
  input [15:0]M_AXI_HPM1_FPD_0_rid;
  input M_AXI_HPM1_FPD_0_rlast;
  output M_AXI_HPM1_FPD_0_rready;
  input [1:0]M_AXI_HPM1_FPD_0_rresp;
  input M_AXI_HPM1_FPD_0_rvalid;
  output [31:0]M_AXI_HPM1_FPD_0_wdata;
  output M_AXI_HPM1_FPD_0_wlast;
  input M_AXI_HPM1_FPD_0_wready;
  output [3:0]M_AXI_HPM1_FPD_0_wstrb;
  output M_AXI_HPM1_FPD_0_wvalid;
  output [93:0]emio_enet0_enet_tsu_timer_cnt_0;
  input maxihpm0_fpd_aclk_0;
  input maxihpm1_fpd_aclk_0;
  output pl_clk0_0;
  input [0:0]pl_ps_irq0_0;
  output pl_resetn0_0;

  wire [39:0]M_AXI_HPM0_FPD_0_araddr;
  wire [1:0]M_AXI_HPM0_FPD_0_arburst;
  wire [3:0]M_AXI_HPM0_FPD_0_arcache;
  wire [15:0]M_AXI_HPM0_FPD_0_arid;
  wire [7:0]M_AXI_HPM0_FPD_0_arlen;
  wire M_AXI_HPM0_FPD_0_arlock;
  wire [2:0]M_AXI_HPM0_FPD_0_arprot;
  wire [3:0]M_AXI_HPM0_FPD_0_arqos;
  wire M_AXI_HPM0_FPD_0_arready;
  wire [2:0]M_AXI_HPM0_FPD_0_arsize;
  wire [15:0]M_AXI_HPM0_FPD_0_aruser;
  wire M_AXI_HPM0_FPD_0_arvalid;
  wire [39:0]M_AXI_HPM0_FPD_0_awaddr;
  wire [1:0]M_AXI_HPM0_FPD_0_awburst;
  wire [3:0]M_AXI_HPM0_FPD_0_awcache;
  wire [15:0]M_AXI_HPM0_FPD_0_awid;
  wire [7:0]M_AXI_HPM0_FPD_0_awlen;
  wire M_AXI_HPM0_FPD_0_awlock;
  wire [2:0]M_AXI_HPM0_FPD_0_awprot;
  wire [3:0]M_AXI_HPM0_FPD_0_awqos;
  wire M_AXI_HPM0_FPD_0_awready;
  wire [2:0]M_AXI_HPM0_FPD_0_awsize;
  wire [15:0]M_AXI_HPM0_FPD_0_awuser;
  wire M_AXI_HPM0_FPD_0_awvalid;
  wire [15:0]M_AXI_HPM0_FPD_0_bid;
  wire M_AXI_HPM0_FPD_0_bready;
  wire [1:0]M_AXI_HPM0_FPD_0_bresp;
  wire M_AXI_HPM0_FPD_0_bvalid;
  wire [31:0]M_AXI_HPM0_FPD_0_rdata;
  wire [15:0]M_AXI_HPM0_FPD_0_rid;
  wire M_AXI_HPM0_FPD_0_rlast;
  wire M_AXI_HPM0_FPD_0_rready;
  wire [1:0]M_AXI_HPM0_FPD_0_rresp;
  wire M_AXI_HPM0_FPD_0_rvalid;
  wire [31:0]M_AXI_HPM0_FPD_0_wdata;
  wire M_AXI_HPM0_FPD_0_wlast;
  wire M_AXI_HPM0_FPD_0_wready;
  wire [3:0]M_AXI_HPM0_FPD_0_wstrb;
  wire M_AXI_HPM0_FPD_0_wvalid;
  wire [39:0]M_AXI_HPM1_FPD_0_araddr;
  wire [1:0]M_AXI_HPM1_FPD_0_arburst;
  wire [3:0]M_AXI_HPM1_FPD_0_arcache;
  wire [15:0]M_AXI_HPM1_FPD_0_arid;
  wire [7:0]M_AXI_HPM1_FPD_0_arlen;
  wire M_AXI_HPM1_FPD_0_arlock;
  wire [2:0]M_AXI_HPM1_FPD_0_arprot;
  wire [3:0]M_AXI_HPM1_FPD_0_arqos;
  wire M_AXI_HPM1_FPD_0_arready;
  wire [2:0]M_AXI_HPM1_FPD_0_arsize;
  wire [15:0]M_AXI_HPM1_FPD_0_aruser;
  wire M_AXI_HPM1_FPD_0_arvalid;
  wire [39:0]M_AXI_HPM1_FPD_0_awaddr;
  wire [1:0]M_AXI_HPM1_FPD_0_awburst;
  wire [3:0]M_AXI_HPM1_FPD_0_awcache;
  wire [15:0]M_AXI_HPM1_FPD_0_awid;
  wire [7:0]M_AXI_HPM1_FPD_0_awlen;
  wire M_AXI_HPM1_FPD_0_awlock;
  wire [2:0]M_AXI_HPM1_FPD_0_awprot;
  wire [3:0]M_AXI_HPM1_FPD_0_awqos;
  wire M_AXI_HPM1_FPD_0_awready;
  wire [2:0]M_AXI_HPM1_FPD_0_awsize;
  wire [15:0]M_AXI_HPM1_FPD_0_awuser;
  wire M_AXI_HPM1_FPD_0_awvalid;
  wire [15:0]M_AXI_HPM1_FPD_0_bid;
  wire M_AXI_HPM1_FPD_0_bready;
  wire [1:0]M_AXI_HPM1_FPD_0_bresp;
  wire M_AXI_HPM1_FPD_0_bvalid;
  wire [31:0]M_AXI_HPM1_FPD_0_rdata;
  wire [15:0]M_AXI_HPM1_FPD_0_rid;
  wire M_AXI_HPM1_FPD_0_rlast;
  wire M_AXI_HPM1_FPD_0_rready;
  wire [1:0]M_AXI_HPM1_FPD_0_rresp;
  wire M_AXI_HPM1_FPD_0_rvalid;
  wire [31:0]M_AXI_HPM1_FPD_0_wdata;
  wire M_AXI_HPM1_FPD_0_wlast;
  wire M_AXI_HPM1_FPD_0_wready;
  wire [3:0]M_AXI_HPM1_FPD_0_wstrb;
  wire M_AXI_HPM1_FPD_0_wvalid;
  wire [93:0]emio_enet0_enet_tsu_timer_cnt_0;
  wire maxihpm0_fpd_aclk_0;
  wire maxihpm1_fpd_aclk_0;
  wire pl_clk0_0;
  wire [0:0]pl_ps_irq0_0;
  wire pl_resetn0_0;

  dual_hpm dual_hpm_i
       (.M_AXI_HPM0_FPD_0_araddr(M_AXI_HPM0_FPD_0_araddr),
        .M_AXI_HPM0_FPD_0_arburst(M_AXI_HPM0_FPD_0_arburst),
        .M_AXI_HPM0_FPD_0_arcache(M_AXI_HPM0_FPD_0_arcache),
        .M_AXI_HPM0_FPD_0_arid(M_AXI_HPM0_FPD_0_arid),
        .M_AXI_HPM0_FPD_0_arlen(M_AXI_HPM0_FPD_0_arlen),
        .M_AXI_HPM0_FPD_0_arlock(M_AXI_HPM0_FPD_0_arlock),
        .M_AXI_HPM0_FPD_0_arprot(M_AXI_HPM0_FPD_0_arprot),
        .M_AXI_HPM0_FPD_0_arqos(M_AXI_HPM0_FPD_0_arqos),
        .M_AXI_HPM0_FPD_0_arready(M_AXI_HPM0_FPD_0_arready),
        .M_AXI_HPM0_FPD_0_arsize(M_AXI_HPM0_FPD_0_arsize),
        .M_AXI_HPM0_FPD_0_aruser(M_AXI_HPM0_FPD_0_aruser),
        .M_AXI_HPM0_FPD_0_arvalid(M_AXI_HPM0_FPD_0_arvalid),
        .M_AXI_HPM0_FPD_0_awaddr(M_AXI_HPM0_FPD_0_awaddr),
        .M_AXI_HPM0_FPD_0_awburst(M_AXI_HPM0_FPD_0_awburst),
        .M_AXI_HPM0_FPD_0_awcache(M_AXI_HPM0_FPD_0_awcache),
        .M_AXI_HPM0_FPD_0_awid(M_AXI_HPM0_FPD_0_awid),
        .M_AXI_HPM0_FPD_0_awlen(M_AXI_HPM0_FPD_0_awlen),
        .M_AXI_HPM0_FPD_0_awlock(M_AXI_HPM0_FPD_0_awlock),
        .M_AXI_HPM0_FPD_0_awprot(M_AXI_HPM0_FPD_0_awprot),
        .M_AXI_HPM0_FPD_0_awqos(M_AXI_HPM0_FPD_0_awqos),
        .M_AXI_HPM0_FPD_0_awready(M_AXI_HPM0_FPD_0_awready),
        .M_AXI_HPM0_FPD_0_awsize(M_AXI_HPM0_FPD_0_awsize),
        .M_AXI_HPM0_FPD_0_awuser(M_AXI_HPM0_FPD_0_awuser),
        .M_AXI_HPM0_FPD_0_awvalid(M_AXI_HPM0_FPD_0_awvalid),
        .M_AXI_HPM0_FPD_0_bid(M_AXI_HPM0_FPD_0_bid),
        .M_AXI_HPM0_FPD_0_bready(M_AXI_HPM0_FPD_0_bready),
        .M_AXI_HPM0_FPD_0_bresp(M_AXI_HPM0_FPD_0_bresp),
        .M_AXI_HPM0_FPD_0_bvalid(M_AXI_HPM0_FPD_0_bvalid),
        .M_AXI_HPM0_FPD_0_rdata(M_AXI_HPM0_FPD_0_rdata),
        .M_AXI_HPM0_FPD_0_rid(M_AXI_HPM0_FPD_0_rid),
        .M_AXI_HPM0_FPD_0_rlast(M_AXI_HPM0_FPD_0_rlast),
        .M_AXI_HPM0_FPD_0_rready(M_AXI_HPM0_FPD_0_rready),
        .M_AXI_HPM0_FPD_0_rresp(M_AXI_HPM0_FPD_0_rresp),
        .M_AXI_HPM0_FPD_0_rvalid(M_AXI_HPM0_FPD_0_rvalid),
        .M_AXI_HPM0_FPD_0_wdata(M_AXI_HPM0_FPD_0_wdata),
        .M_AXI_HPM0_FPD_0_wlast(M_AXI_HPM0_FPD_0_wlast),
        .M_AXI_HPM0_FPD_0_wready(M_AXI_HPM0_FPD_0_wready),
        .M_AXI_HPM0_FPD_0_wstrb(M_AXI_HPM0_FPD_0_wstrb),
        .M_AXI_HPM0_FPD_0_wvalid(M_AXI_HPM0_FPD_0_wvalid),
        .M_AXI_HPM1_FPD_0_araddr(M_AXI_HPM1_FPD_0_araddr),
        .M_AXI_HPM1_FPD_0_arburst(M_AXI_HPM1_FPD_0_arburst),
        .M_AXI_HPM1_FPD_0_arcache(M_AXI_HPM1_FPD_0_arcache),
        .M_AXI_HPM1_FPD_0_arid(M_AXI_HPM1_FPD_0_arid),
        .M_AXI_HPM1_FPD_0_arlen(M_AXI_HPM1_FPD_0_arlen),
        .M_AXI_HPM1_FPD_0_arlock(M_AXI_HPM1_FPD_0_arlock),
        .M_AXI_HPM1_FPD_0_arprot(M_AXI_HPM1_FPD_0_arprot),
        .M_AXI_HPM1_FPD_0_arqos(M_AXI_HPM1_FPD_0_arqos),
        .M_AXI_HPM1_FPD_0_arready(M_AXI_HPM1_FPD_0_arready),
        .M_AXI_HPM1_FPD_0_arsize(M_AXI_HPM1_FPD_0_arsize),
        .M_AXI_HPM1_FPD_0_aruser(M_AXI_HPM1_FPD_0_aruser),
        .M_AXI_HPM1_FPD_0_arvalid(M_AXI_HPM1_FPD_0_arvalid),
        .M_AXI_HPM1_FPD_0_awaddr(M_AXI_HPM1_FPD_0_awaddr),
        .M_AXI_HPM1_FPD_0_awburst(M_AXI_HPM1_FPD_0_awburst),
        .M_AXI_HPM1_FPD_0_awcache(M_AXI_HPM1_FPD_0_awcache),
        .M_AXI_HPM1_FPD_0_awid(M_AXI_HPM1_FPD_0_awid),
        .M_AXI_HPM1_FPD_0_awlen(M_AXI_HPM1_FPD_0_awlen),
        .M_AXI_HPM1_FPD_0_awlock(M_AXI_HPM1_FPD_0_awlock),
        .M_AXI_HPM1_FPD_0_awprot(M_AXI_HPM1_FPD_0_awprot),
        .M_AXI_HPM1_FPD_0_awqos(M_AXI_HPM1_FPD_0_awqos),
        .M_AXI_HPM1_FPD_0_awready(M_AXI_HPM1_FPD_0_awready),
        .M_AXI_HPM1_FPD_0_awsize(M_AXI_HPM1_FPD_0_awsize),
        .M_AXI_HPM1_FPD_0_awuser(M_AXI_HPM1_FPD_0_awuser),
        .M_AXI_HPM1_FPD_0_awvalid(M_AXI_HPM1_FPD_0_awvalid),
        .M_AXI_HPM1_FPD_0_bid(M_AXI_HPM1_FPD_0_bid),
        .M_AXI_HPM1_FPD_0_bready(M_AXI_HPM1_FPD_0_bready),
        .M_AXI_HPM1_FPD_0_bresp(M_AXI_HPM1_FPD_0_bresp),
        .M_AXI_HPM1_FPD_0_bvalid(M_AXI_HPM1_FPD_0_bvalid),
        .M_AXI_HPM1_FPD_0_rdata(M_AXI_HPM1_FPD_0_rdata),
        .M_AXI_HPM1_FPD_0_rid(M_AXI_HPM1_FPD_0_rid),
        .M_AXI_HPM1_FPD_0_rlast(M_AXI_HPM1_FPD_0_rlast),
        .M_AXI_HPM1_FPD_0_rready(M_AXI_HPM1_FPD_0_rready),
        .M_AXI_HPM1_FPD_0_rresp(M_AXI_HPM1_FPD_0_rresp),
        .M_AXI_HPM1_FPD_0_rvalid(M_AXI_HPM1_FPD_0_rvalid),
        .M_AXI_HPM1_FPD_0_wdata(M_AXI_HPM1_FPD_0_wdata),
        .M_AXI_HPM1_FPD_0_wlast(M_AXI_HPM1_FPD_0_wlast),
        .M_AXI_HPM1_FPD_0_wready(M_AXI_HPM1_FPD_0_wready),
        .M_AXI_HPM1_FPD_0_wstrb(M_AXI_HPM1_FPD_0_wstrb),
        .M_AXI_HPM1_FPD_0_wvalid(M_AXI_HPM1_FPD_0_wvalid),
        .emio_enet0_enet_tsu_timer_cnt_0(emio_enet0_enet_tsu_timer_cnt_0),
        .maxihpm0_fpd_aclk_0(maxihpm0_fpd_aclk_0),
        .maxihpm1_fpd_aclk_0(maxihpm1_fpd_aclk_0),
        .pl_clk0_0(pl_clk0_0),
        .pl_ps_irq0_0(pl_ps_irq0_0),
        .pl_resetn0_0(pl_resetn0_0));
endmodule
