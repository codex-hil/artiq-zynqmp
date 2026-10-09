# Genesys Si5342 diagnostics

These diagnostics reuse AMD's maintained XIicPs implementation from the
already reproduced standalone Ethernet BSP. They address IC46 (GTH clock),
not IC67 (PS clock). No Vitis installation or new I2C driver is required.
The original Digilent repositories remain unchanged.

## Read-only backup

Build inside the shared Vivado Ubuntu environment:

```sh
vivado-container shell -c 'exec "$@"' bash \
  /srv/codex-hil-data/artiq-zynqmp/work/artiq-new-wip/diagnostics/si5342/build_readout.sh \
  /srv/codex-hil-data/artiq-zynqmp/build/si5342-readout
```

After exact-cable PS reset and the matching DMA PMU/FSBL startup, load
`si5342-readout.elf` on A53 CPU0 with `scripts/run_ethernet.tcl` (this script
only starts an ELF; the diagnostic itself does not start Ethernet).
Capture Genesys UART at115200 baud, then run:

```sh
python diagnostics/si5342/parse_readout.py uart.log backup.json
```

The parser requires3072 unique addresses, Si5342 identity, all12 page
selectors and the firmware completion marker. A dump with duplicated page0
must fail. Compare a repeated readout; dynamic diagnostic registers can vary.
Evidence: `evidence/si5342-readout-2026-10-09.json`.

Transport: PS I2C0 at0xff020000, main mux0x70, channel2 (control0x04),
Si5342 address0x68. Every downstream transaction first reads the mux using
repeated START, following Digilent's multi-master arbitration rules. A mux
channel write must end with STOP before use. The driver must allow bus-idle
completion before another transfer. Physical trials also required100us
settling after a held one-byte receive before changing direction to TX.
Page writes finish separately; register-pointer/read remains one transaction.
Only mux and page/pointer writes occur in the backup utility.

References:

- [Digilent board manual](https://digilent.com/reference/programmable-logic/genesys-zu/reference-manual), clocking and main I2C bus sections.
- [Si5342 Rev-D register manual](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/reference-manuals/Si5345-44-42-D-RM.pdf), section17.
- Digilent genesys-zu-sw commit6d783aab93dc4586bf6c06921808aa53517e1689,
  `src/5ev_hdmi_demo/src/si5432_axi.c` (filename typo; device is Si5342).
  Its148.5MHz HDMI profile must not be applied unchanged to this GTH setup.
