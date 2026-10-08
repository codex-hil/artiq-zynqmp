# RTIO DMA bring-up

The existing Piotr PS/PL CSR path is preserved. Variant `local-rtio-dma`
adds the noncoherent PS S_AXI_HP0_FPD port (saxigp2), 64-bit data and
49-bit address. No LiteX SoC migration. The current SD image remains the
validated non-DMA image until a new firmware/image passes acceptance.

DMA implementation is adapted from pinned M-Labs artiq-zynq, with original
SHA/license in `1_gateware/DMA_ORIGIN.json` and `DMA_LICENSE`. RecordSlicer,
TimeOffset and CRIMaster are unchanged upstream ARTIQ. CRISwitch selects
kernel or DMA master. Existing banks0/1/2 remain fixed; DMA bank3 and CRI
selector bank4 are added. Record format remains upstream ARTIQ; no CPU
pulse-replay emulation. Same-ID AXI reads require ordered responses.

RTL tests (not hardware evidence):

```sh
make test-sim PYTHON=/srv/codex-hil-data/artiq-zynqmp/venv/bin/python
```

`test_zynqmp_dma.py` validates AXI memory reads, multi-record replay with
backpressure, TTL timing through the real RTIO core, AXI SLVERR latching and
clearing at next playback. Timestamps and data cross record/beat boundaries.

Physical direct-engine test, after booting matching PS/PL configuration,
with CPU1 idle and JB1-JB2 jumper present:

```sh
python3 scripts/test_dma_jtag_hw.py --csr-map DMA_CSR_MAP \
  --server SERVER --cable 210383B7F02DA --output LARGE_DISK_TEST_OUTPUT
```

Reserves DDR0x22000000 for trace. DAP writes standard records into DDR,
starts hardware reader, checks bounded completion and DMA/AXI errors,
then checks eight actual loopback timestamps for four100us pulses. Only
DDR buffer fill/control uses DAP; FPGA performs playback independently.
The probe resets local RTIO, so run with no concurrent kernel/experiment.

CoreDMA recording/named persistent buffers/handles and exception exports
are not integrated yet; direct engine validation is not a CoreDMA API PASS.
