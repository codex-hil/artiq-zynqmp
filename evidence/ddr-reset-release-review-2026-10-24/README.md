# Reset/release source audit — 2026-10-24

Offline only. UG1085v2.5 APU Clocks and Resets explicitly distinguishes APU reset
from graceful request termination: APU reset does not gracefully finish traffic
to/from that subsystem. Thus debugger stop, CPU reset and APU reset-control
samples cannot serve as a DDR transaction-drain acknowledgment.

UG1085 PMU Reset printed p113 distinguishes POR from SRST. SRST preserves much
local/global register and PS power state; POR has broader initialization. The
existing XSDB rst -system action was not independently mapped to every relevant
interconnect reset/completion domain in this audit. Do not silently substitute
power-cycle/POR or assume a full cold transaction epoch from its command name.
Primary source:
https://docs.amd.com/api/khub/documents/xzMsp_c5sG9J6A3u7NkJYQ/content?Ft-Calling-App=ft

Exact FSBL source: xfsbl_initialization.c:967-971 JTAG boot returns STATUS_JTAG.
xfsbl_main.c:155 onward sets both R5 usage-status bits and transitions to STAGE4,
bypassing ordinary STAGE3 partition loading. Usage bits are software policy,
not NCPUHALT/reset or instruction-execution status. xfsbl_handoff.c contains
processor-specific reset releases for ordinary handoffs; their presence in the
source does not prove those branches ran in the JTAG diagnostic boot. Existing
checked FSBL terminal and sampled reset controls remain stronger observed facts.

Existing launchers stop four A53 cores with caught stop errors, select alternate
JTAG, system-reset, then PMU and CPU0 FSBL. RPU is not explicitly parked by that
sequence. No new reset or halt action was selected here. Positive CPU0 terminal
and APU reset0x300e/RPU NCPUHALT0 snapshots do not exclude future ROM/PMU releases.

Separate obligations before any DDR write:
1. Current core execution held outside the tested memory, with exact boot identity.
2. Future reset-release/wakeup authority excluded or contained for that window.
3. All previously accepted transactions completed or canceled by a documented
   reset-domain sequence, plus no new admitted master traffic.

No extra idle snapshot closes these three. Next offline inspect actual PMU RPU
sleep/wake/reset state transitions and available documented interconnect drain/
reset-domain guarantees. Derive a concrete candidate only after that review;
do not add arbitrary resets or mask errors to make sampled fields quiet.
Full DDR NOT_RUN/NOT_ADMITTED; normal runtime unchanged, no fresh health check.
