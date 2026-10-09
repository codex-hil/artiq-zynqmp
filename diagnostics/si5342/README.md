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

## RX recovered-clock lock

The clock-forward top is an optional extension of the existing GTH
PRBS diagnostic, not a DRTIO satellite. A2/A1 drive the AC-coupled
SFP_REC_CLK input to Si5342 IN0 through ODDRE1/OBUFDS. BUFGCTRL can
select the independent PS125MHz bootstrap clock for startup/control.
Both physical TX/RX clock counters must advance and settled PRBS7 error
counts must remain unchanged; resetdone flags alone are insufficient.

Build a fresh diagnostic with the existing PS and156.25MHz GTH exports:

```sh
FORWARD_RX_CLOCK=1 diagnostics/drtio/build_top.sh \
  /srv/codex-hil-data/artiq-zynqmp/build-vivado/genesys-rtio-dma \
  /srv/codex-hil-data/artiq-zynqmp/build/drtio-phy-2026-10-08/final156 \
  /srv/codex-hil-data/artiq-zynqmp/build-vivado/drtio-clock-forward-new
make si5342-control O=/srv/codex-hil-data/artiq-zynqmp/build/si5342-new
make test-si5342
```

The validated2026-10-09 artifacts are already available in
`build-vivado/drtio-clock-select-2026-10-09` and
`build/si5342-2026-10-09/si5342-control.elf` under the project data root.
Use the current hw_server address; Docker container IPs change on restart.
For those artifacts, from the repository root:

```sh
project_data=/srv/codex-hil-data/artiq-zynqmp
python_bin="$project_data/venv/bin/python"
"$python_bin" diagnostics/si5342/load_diagnostic.py \
  --server tcp:172.17.0.3:3121 --cable 210383B7F02DA \
  --port /dev/serial/by-id/usb-Digilent_Digilent_Adept_USB_Device_210383B7F02D-if01-port0 \
  --ps-export "$project_data/build-vivado/dma-ps-2025.2" \
  --bitstream "$project_data/build-vivado/drtio-clock-select-2026-10-09/top.bit" \
  --csr-map "$project_data/build-vivado/drtio-clock-select-2026-10-09/csr-map.json" \
  --service-elf "$project_data/build/si5342-2026-10-09/si5342-control.elf" \
  --output "$project_data/build/si5342-retest/load"
make test-hw-si5342 PYTHON="$python_bin" JTAG_SERVER=tcp:172.17.0.3:3121 \
  CSR_MAP="$project_data/build-vivado/drtio-clock-select-2026-10-09/csr-map.json" \
  O="$project_data/build/si5342-retest"
```

The loader resets only the identified Genesys, starts matching PMU/FSBL,
configures PL, initializes AXI, verifies the PHY and starts the temporary
UART register service. The hardware test performs a volatile Si5342 reset,
verifies the factory output plan, saves every modified register, loads
`profile-rx125.json`, then checks independent PS lock and actual RX lock.
It performs three clock-off/on cycles. Each phase requires five consecutive
status samples; GTH verification checks zero new PRBS errors and both clock
ratios within1000ppm of the PS counter. Acquisition errors are excluded.
The saved volatile settings are restored in `finally`. No OTP programming
or boot-flash writes occur. A reset-trigger transaction can NACK as the
chip restarts; device-ready/identity checks must subsequently pass.

Nominal plan: IN0=125MHz, P0=63, M=1386, Fpfd=125MHz/63,
VCO=13.75GHz, N0=44, R0=2, OUT0=156.25MHz. The factory MXAXB, N/R
and electrical output settings are preserved. Retaining156.25MHz is
necessary for the current GTH IP; RX user clock is125MHz at2.5Gbps raw20.
The profile reuses Digilent DSPLL coefficients and timing, with a PFD close
to its original1.98MHz. It is an experimental laboratory profile, not a
new ClockBuilder-Pro-certified production configuration. The extended OOF
thresholds use a nominal500ppm set/450ppm clear interpretation of the
manual's1/16ppm encoding; that window is not independently calibrated.
The detector stays enabled. Absolute frequency, jitter, remote-master
tracking and deterministic latency have not been measured by this test.
A self-referential GTH loop is not an external source of accurate time.

Compatibility findings: mux0x74 was incorrect (the main mux is0x70);
back-to-back transfers before STOP completed prevented mux selection;
held RX-to-TX transfers required the settling guard; page selection must
be verified; the original HDMI input2 clock gates cannot be copied unchanged
to input0; integer and fractional divider modes require consistent clock
settings. P0=25/M=550 produced intermittent acquisition/recovery;
P0=63/M=1386 keeps the PFD near the original generated profile. An extra
outer-loop reset after the global configuration reset was removed. Si5342
reconfiguration can stop GTH TX even while resetdone remains high, so the
GTH reset and clock-counter checks are mandatory.

Restore the normal core afterward using the existing [CoreDMA boot flow](../../docs/CORE_DMA.md)
and matching local RTIO PL/CPU1/CPU0 artifacts. The hardware test restores
Si5342 settings, but leaves the diagnostic PL and UART service loaded.

## Autonomous firmware clock manager

`autoclock.c` reuses the validated AMD XIicPs transport and JSON-derived
P0=63/M=1386 laboratory profile. It runs on CPU0 in the separate GTH
clock-forward diagnostic, independently of host register commands:

1. Verify Si5342 identity, factory frequency plan and diagnostic CSR magic.
2. Save touched volatile registers and configure the existing profile.
3. Seed IN0 with the independent PS 125 MHz clock and wait for stable lock.
4. Reset/reacquire GTH, switch IN0 to RXCLK, verify stable lock and actual
   TX/RX clock counters with zero new settled PRBS7 errors.
5. On loss, return to PS clock and repeat acquisition. A UART `L` command
   physically removes IN0 for one second as a negative control; `Q` restores
   the saved registers and disables forwarding.

```sh
vivado-container shell -c 'export SI_SOURCE=autoclock; exec "$@"' bash \
  diagnostics/si5342/build_readout.sh /path/to/autoclock
python diagnostics/si5342/test_autoclock_hw.py \
  --server tcp:SERVER:3121 --cable YOUR_GENESYS_SERIAL \
  --port /dev/serial/by-id/YOUR_GENESYS_UART \
  --elf /path/to/autoclock/si5342-autoclock.elf --output /path/to/evidence
```

Physical startup, three loss/recovery cycles and volatile register restore
passed on 2026-10-09. This is autonomous **diagnostic firmware**, not yet
integration with the ARTIQ satellite runtime. It does not resynchronize RTIO
time, implement remote link selection or measure jitter. Loss recovery
resets GTH; packet traffic must be retrained at a later integration stage.
