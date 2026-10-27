# Actual PMU time/MMIO backend contract review — 2026-10-27

Offline source/library/document review, no HW access or register writes.
Installed xtimer_config.h selects default MB sleep and NO_TICK_TIMER. Compiled
libxiltimer.a has XilSleepTimer_Init/XilTickTimer_Init but no defined XTime_GetTime;
API declaration alone is not usable counter implementation. MB sleep source
uses frequency-scaled delay loops, not a measured free-running64bit timestamp.

PMU scheduler initializes PIT1 (not PIT0). Source selects10ms reload and control3;
software Tick increments in interrupt handler. Guard clears IE, so software Tick
cannot provide a progressing deadline there. Raw PIT1 is32bit/reloading and is
already scheduler-owned; two samples do not identify missed wraps. SDT derives
reload from XGet_CpuFreq, not a physically qualified constant assumed by this work.
No unused PIT channel is claimed or reconfigured.

Xil_In32 is one volatile load; ordinary Xil_Out32 is one volatile store. They do
not supply callback success/error status or preempt a hung access. Bus errors can
enter processor/ROM exception behavior, not return an ordinary negative callback
code. A C wrapper always returning0 after these primitives would misrepresent
fault handling. Software deadline checks only occur when callbacks return.

UG1085v2.5p363 Table15-1 lists five ATB instances. No reviewed proof maps and
confirms enabled response/timeout for PMU->LPD_SLCR AIB register accesses. Do not
assume global ATB coverage or program new ATB policy. p363 formula is conditional
on actual bus clock,prescale and enable; those values were not captured.
Official source previously inspected:
https://docs.amd.com/api/khub/documents/xzMsp_c5sG9J6A3u7NkJYQ/content?Ft-Calling-App=ft

Physical backend readiness is FALSE: timer/units/rollover, bus bounded completion,
exception/fault receipt and acceptance-uncertain write policy remain unqualified.
Session/deadline host tests and target audit stay valid for abstract callbacks,
not as hardware readiness proof. Retain request on uncertain effect; no blind clear.

Next offline inventory PIT0..3 ownership/control and available counter paths from
maintained PMU/ROM/BSP sources, then select a read-only timer observation plan if
it can add evidence without disrupting scheduler/ROM. In parallel map exact AIB
register access route before choosing any transport fault mechanism. No AIB/MMIO
write candidate or physical experiment admitted; normal runtime unchanged.
DDR remains NOT_RUN/NOT_ADMITTED.
