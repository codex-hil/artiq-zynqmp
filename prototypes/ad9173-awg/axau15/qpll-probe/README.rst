AXAU15 dedicated-reference QPLL diagnostic
=========================================

Offline diagnostic, no hardware qualification. Inherits the electrical gate
from ../refclk-probe: confirm actual carrier/module series AC capacitors on
FMC GBTCLK0 before enabling HMC output12. The new public ACAU15 manual and
fpgauk/axau15 repository do not supply the missing full schematic. No hardware
access, HMC writes or FPGA programming is performed by these build/test files.

The pinned LiteICLink GTH4QuadPLL configures QPLL1 N100/M2 from245.76MHz,
VCO12.288GHz. This is the candidate configuration for6.144Gb/s with channel
output divider2; this diagnostic instantiates NO GT channels or JESD logic.
System200MHz -> BUFGCE_DIV2 provides lock detection at100MHz and a1024-cycle
startup reset independent of the FMC reference. DRP writes are tied off.
FMC V7/V6 -> IBUFDS_GTE4 O -> QPLL; ODIV2 explicitly /2 -> BUFG_GT -> counter.
No fabric GTGREFCLK route or CLOCK_DEDICATED_ROUTE override.

USER1 captures high word0x41585130 OR synchronized lock bit0, low word Gray
counter. USER2 retains qualified clock-setup GPIOv2. read.tcl requires three
consecutive locked/advancing captures. It only reads JTAG, must run within an
ALINX-only leased session, and neither loads an image nor enables reference.
The readout is activity/lock evidence, not calibrated frequency or jitter.

Reproduce
---------

Generate qpll_common.v and qpll.json in this directory using the existing
jesd-venv Python and generate.py. Dependencies are pinned in ../../dependencies.json.
Copy core.v, top.v, qpll_common.v and build.tcl to a new Dell job directory and
run Vivado2025.2 under the global build lease. No hardware operation on Dell.

Logic simulation with Icarus (exclude qpll_common.v; tb.v supplies explicit
non-analog models)::

    iverilog -g2012 -s tb -o sim.vvp core.v top.v tb.v
    vvp sim.vvp

The test checks reset duration, signature/lock synchronization, injected lock
loss, clock stop/restart and Gray encoding. It cannot establish physical PLL
lock, GTH behavior, metastability MTBF or vendor primitive timing.

Future hardware sequence: establish coupling/driver mode, hold DAC muted,
load under ALINX lease, enable qualified HMC reference, check clock activity
and lock, then bounded reference-off/on and reset recovery. Build success is
not permission to skip the electrical prerequisite.

Placement audit
---------------

The unconstrained initial build placed the common in neighboring X0Y0 while
V7/V6 maps to IBUFDS_GTE4 at X0Y1. The final build explicitly LOCs the QPLL
common to GTHE4_COMMON_X0Y1 (bank225). audit.tcl checks both sites and N/M on
the routed checkpoint. This avoids qualifying a diagnostic in another quad
than the future four-lane JESD transmitter. Initial build was never programmed.

Final implementation: Dell alinx-qpll-probe-20261023b, setup6.732ns,
hold0.046ns, bus-skew slack7.233ns, DRC0 errors. New-top logic-only simulation
PASS; physical QPLL/refclk/JESD NOT_RUN. Evidence under
../../evidence/axau15/qpll-probe-20261023/.
