# DDR diagnostic boot-window ownership

The intended DDR test window is **after the SPD-trained FSBL JTAG terminal and
before CPU0 network runtime or CPU1 kernel worker starts**. The observer and its
exception vectors execute in OCM. This window is not yet admitted for DDR writes.

Offline source/image audit: `evidence/fsbl-network-window-2026-10-23`.
Reproduce with `scripts/audit_fsbl_network_window.py --build BUILD --output FRESH`.
The audited FSBL/PMU hashes match the diagnostic images in the trained-observer
manifest. Neither ELF has named XEmacPs/lwIP/netif entry points. That is negative
symbol evidence, not proof of absence of generic MMIO or ROM-mediated actions.
The adjacent source tree has not been independently rebuilt to prove equivalence.

In `xfsbl_initialization.c`, JTAG returns `XFSBL_STATUS_JTAG` before device-driver
initialization. `xfsbl_main.c` takes this status to stage4/handoff and marks both
RPU cores usable in its usage-status register. That usage marker is not a reset
or halted-core certificate. The generated `psu_init.c` enables GEM clocks and
releases GEM0 reset. PMU contains a GEM reset definition using a ROM callback;
its continued reset/clock authority must not be mistaken for an absent master.
No new stop/reset policy is authorized by this document alone.

## Required integration before any DDR writer

1. Keep the existing shared Genesys lease from system reset through normal-runtime
   restoration and physical validation. Preserve storage gates and artifact pins.
2. Establish actual JTAG/diagnostic boot mode and checked FSBL terminal/CPU0 state;
   UART text alone is insufficient. Do not start normal runtime or CPU1 worker.
3. Collect existing fixed GEM/SD/QSPI, CSU, ZDMA and RPU register observations
   **within this same window**, after training. Associate every capture with the
   same manifest and boot session; prior runtime snapshots do not qualify.
4. Require GEM RX/TX disabled at this point. If enabled, reject and restore;
   do not silently call XEmacPs_Stop, clear flags or guess a drain delay. Disabled
   bits are necessary observations, not standalone proof of outstanding drain.
5. Resolve secondary A53/R5, PMU, PL HP0, PCAP and remaining PS master ownership.
   Prove reset ordering/drain separately. The actual DMA reset counterexample
   shows why IDLE after resetting PL alone is insufficient.
6. Only after explicit admission run a bounded OCM DDR writer with exception
   capture. Preserve the two separate DDR address windows and exclude OCM/MMIO.
7. On any failure restore the qualified normal runtime using the existing parent
   lifecycle; validate TTL/CoreDMA/analyzer/MonInj/Ethernet before lease release.

No physical boot-window peripheral capture or full DDR writer ran in this audit.
The next implementation step is to add read-only observation frames to the
existing trained-observer child, with parent-pinned scripts and offline negative
controls, while keeping the DDR write gate closed.


## Integrated peripheral capture (offline checked)

Use `evidence/boot-peripheral-integration-2026-10-23/inputs.json` as the trained
observer manifest with the existing runtime restoration manifest. It requests
normal exception-observer execution followed by a fixed read-only peripheral
frame. The parent pins nested input manifest, vendor headers and all execution
helpers before and under its lease. Failure rejects the candidate and restores
normal runtime; a quiet result remains observation-only, never DDR admission.
Physical execution remains NOT_RUN at this checkpoint.
