# Sleep guard offline qualification — 2026-10-23

Both explicit guard-enabled and default-disabled AMD PMU images compiled in fresh
isolated directories. The disabled image has no guard function or record.
Linked enabled terminal is mbar 1 at 0xffdc4734, sleep at 0xffdc4738 and bri -4
at 0xffdc473c. The extra publication barrier precedes the sleep/reentry loop.
Wakeup re-enters sleep through the local branch; no scheduler or request dispatch
is reachable through normal terminal control flow. ACK stays zero.

Three unittest cases PASS: actual C host non-return/MSR controls, enabled linked
flow including changed helper/escape/nop/missing-barrier mutations, and disabled
symbol exclusion. Host execution models non-return only, never hardware sleep.

No hardware access. Old failed image and manifests preserved. Existing hardware
gate intentionally still pins old terminal 0xffdc4734 and therefore rejects the
new image. Next: fresh sleep-specific exact gate/manifests and bounded observation
review for wake input residency. Do not run old manifests or force RAM reads.
PMU physical sleep residency, live MSR/guard capture, ROM/NMI paths and exclusive
DDR ownership remain unproven. DDR NOT_ADMITTED. Normal baseline last restored
by prior trial, not freshly checked here.
