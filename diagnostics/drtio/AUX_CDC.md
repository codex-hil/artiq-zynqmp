# PS-clock AUX controller and GTH-clock transmitter

This diagnostic retains ARTIQ's `DRTIOAuxController`, including its Wishbone
SRAM, TX length/start registers and eight-slot RX ring. It does not alter
Piotr's preserved ARTIQ or Migen checkout.

`aux_endpoint.py` connects that controller to the existing raw20 encoder,
link framing and fabric aligner. The controller and its Wishbone interface
remain in `sys`, the PS clock; link TX uses `gth_tx`, link RX and the upstream
RX memory writer use `rtio_rx` (to be mapped to the physical recovered clock).

`aux_tx_cdc.py` buffers the entire packet before making it visible to TX.
A 4096-entry, 5-bit asynchronous FIFO stores up to 2048 nibbles plus an
end marker. A synchronized request/completion toggle permits one packet
in flight. Link TX can pause FIFO consumption during RT traffic. The
controller's original TX-busy register describes enqueue completion;
**firmware must also wait for bridge `busy` to clear before another start**.
The eventual hardware CSR map must expose that additional condition.

After comma alignment, RX waits 127 recovered-clock cycles for codec and
scrambler convergence before admitting samples to the AUX ring. Without
this quarantine, unrelated-clock simulation catches a bogus first packet.

Both domains must reset together. Independent GT reset while PS stays live
is not supported by this diagnostic: integration must abort/reset the
bridge coherently. No production reset/relock claim is made.

Run from the repository with the documented Migen/MiSoC environment:

```sh
make test-drtio-aux-cdc PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python
```

The tests cover faster/slower PS clocks, a full 1024-byte packet, ring wrap,
misaligned raw serial words, RT arbitration, ring overflow and recovery.
They are simulation evidence only. Top-level AXI address decoding, additional
CDC constraints, Vivado build, physical AUX SRAM transfers and firmware
protocol/discovery/routing are still pending. No board is reset or programmed
by this test target.

## PS aperture decode and AXI errors

`aux_bus.py` reserves offsets 0x00000–0x03fff for CSR and
0x10000–0x13fff for the upstream AUX SRAM aperture. With the existing
0xa0000000 PS aperture, TX begins at 0xa0010000 and RX slots begin at
0xa0012000. Decode precedes address narrowing. High addresses and gaps do
not select a slave; Wishbone ERR terminates an active invalid transaction.
The original controller's aliases inside its 16 KiB window are preserved.

The installed LiteX AXI-Lite bridge ignores Wishbone ERR and waits only for
ACK, then emits OKAY. `aux_axi.py` provides a shape-checked local overlay of
that existing FSM: completion is ACK or ERR, with a latched SLVERR response
for errors. Only non-low-latency mode is supported. The upstream file is
unchanged; unexpected future FSM shape fails construction explicitly.

`make test-drtio-aux-bus` verifies address boundaries and high-address alias
rejection, real upstream AUX SRAM word accesses, AXI-Lite read/write error
completion, response backpressure, and error-to-success recovery. This is
not yet a full AXI/PS hardware acceptance test. Diagnostic top-level wiring,
CSR exposure and reset/CDC constraints remain next steps.

## Standalone PS integration block

`aux_ps.py` combines full AXI -> upstream AXI-Lite conversion -> checked
Wishbone bridge -> CSR/SRAM router -> the retained AUX endpoint. CSR bank3
begins at 0xa0001800 and exposes TX length/start, RX present/error/pointer,
bridge busy, RX ready and reset status. `generate_aux_ps.py` exports all AXI
channels, raw20 ports and PS/TX/RX clock inputs with a generated map/hash.

The endpoint uses private domains aux_sys/aux_tx/aux_rx. A common asynchronous
reset input drives three FPGA reset synchronizers; deassertion is local to
each clock. The enclosing diagnostic must drive this input from PS reset OR
GT reset/not-ready and hold it through clock restart. AXI/CSR transport
remains alive while the endpoint is held reset. The length CSR is owned by
CSRBank on PS clock and needs an additional explicit synchronous reset.
In-flight CPU transactions must be aborted before reset; active-transfer
reset/relock qualification is still pending.

The pinned MiSoC aligned CSRStorage readback incorrectly inserts
hi-alignment zero bits rather than alignment bits. This makes a valid AUX
length write68 read back512. A checked local readback replacement fixes only
that finalized CSR, without modifying the preserved dependency.

`make test-drtio-aux-ps hdl-drtio-aux-ps` checks full AXI IDs/last/SLVERR,
CSR length/readback, TX SRAM boundaries, reset and error recovery. Its reset
special has a functional simulation override: it does not model or prove
asynchronous assertion/synchronous-release timing. The HDL generator uses
actual Xilinx reset synchronizer lowering. Vivado timing/CDC, connection to
the physical GTH/PS top-level, active-transfer reset and physical AUX tests
remain pending.

## Genesys top-level integration

`diag_gateware.py --aux` now embeds AuxPS in the existing Genesys PS/GTH
platform. It connects HPM0 to the full AXI adapter, raw20 to the physical
GTH IP and retains the monitor in CSR bank0. AUX bank3 and SRAM map are
included in `csr-map.json`. Framing, packet and AUX diagnostics are mutually
exclusive images. SFP TX remains disabled by default.

Common endpoint reset includes PS reset, monitor reset and GT TX/RX
PMA/done/user-clock-active loss. A generated exact first-stage count replaces
the CDC count placeholder. The baseline three counter constraints plus
both 13-bit AUX FIFO Gray pointers give five bus-skew constraints. Vivado
must verify the retained register counts and timing before hardware use.

Build with `DRTIO_AUX=1 diagnostics/drtio/build_top.sh PS_EXPORT PHY_EXPORT
FRESH_OUTPUT` in the documented shared environment. `DRTIO_IP_CACHE` may
point at an existing compatible Vivado cache. Generation alone is not a
passing FPGA build; no AUX image has been loaded on hardware yet.

2026-10-11: Genesys AUX top-level Vivado build PASS, WNS2.696ns/WHS0.011ns,
153 retained CDC bits and five Gray bus-skew constraints. Evidence is in
`evidence/aux-vivado-build-2026-10-11.json`. No AUX hardware test has run.
The next acceptance scope is [AUX_HARDWARE_ACCEPTANCE.md](AUX_HARDWARE_ACCEPTANCE.md).

2026-10-11: physical AUX SRAM/raw20/GTH PMA loopback PASS. Three resets,
30 patterned positive packets (six at1024 bytes), ring wrap, three overflow
controls and recovery. Total57 packets sent,54 readable packets checked,
three deliberate full-ring discards;1704 payload words checked exactly.
No AUX firmware protocol or remote-master claim. Normal core restored;
physical TTL/DMA, analyzer/MonInj and Ethernet regression PASS.

Use `scripts/test_drtio_aux_bringup.py` with the same restoration arguments
as the packet bring-up wrapper, replacing bitstream/map with the passing
AUX build. It holds the exact-board flock over all stages and restoration.
`test_aux_hw.py --dry-run` only emits the Tcl script; no hardware access.
Physical AUX tests can also acquire the board lock themselves; an inherited
wrapper lease is verified and reused. Active-transfer reset remains NOT_RUN
physically because sequential JTAG writes cannot establish that timing.
