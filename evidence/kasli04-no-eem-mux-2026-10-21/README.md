# KASLI04 physically removed EEM mux

User clarified that the electrical fault was repaired and only the EEM
multiplexer is desoldered. Historical mux0x70 NACK is expected absence, not
a current fault of mux0x71/Si5324. The pinned Si5324 driver selects0x70
before0x71, so unmodified runtime would still fail on the removed component.

Added explicit opt-in `--eem-mux-removed` preparation overlay, removing only
the exact0x70 deselection statement. Clock mux0x71 selection, acknowledgement
and Si5324 identity checks remain unchanged. Defaults and prior worktrees
unchanged. One offline test PASS, including exact remaining-source preservation
and rejection of repeated/changed source shape. Isolated source:
`/srv/codex-hil-data/artiq-zynqmp/work/kasli04-no-eem-mux-runtime`.
CPU build launched using the included recipe; not yet qualified at checkpoint.

An attempted FTDI helper import stopped before hardware access because pyftdi
was absent in the chosen environment. No current clock read result exists.
Next use a suitable isolated FTDI environment, then a fixed04-only snapshot
through0x71/Si5324 with saved routing restored; never access missing0x70.
No FPGA/reset/Si-profile/flash changes made in this checkpoint. Runtime still
requires a qualified04 clock snapshot and restoration of its retained SRAM.
