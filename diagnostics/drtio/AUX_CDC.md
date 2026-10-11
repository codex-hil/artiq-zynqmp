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
