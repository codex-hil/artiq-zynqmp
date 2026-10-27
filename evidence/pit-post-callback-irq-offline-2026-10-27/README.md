# Post-callback IRQ state and startup review — offline

32 PIT tests PASS, including actual C optimized+ASan/UBSan with final MSR error,
read callback re-enabling IE, write callback changing another MSR policy bit,
and unchanged-state control. Old source preserved outside Git and compiled with
the same regression fixture: old model assertion fails on incorrect COMPLETE
result for changed IRQ policy. Failure output recorded; no core dump generated.

Lifecycle model now re-reads MSR after collection/publication callbacks return.
It requires exact equality with the verified post-disable MSR; read error or
change maps to IRQ_UNPROVEN before the terminal callback. Initial IRQ failures
remain unproven and do not claim repair. Callback pointers are copied before
entry, but their identity, implementation and truthfulness remain external.

CRITICAL: all three failure controls can coexist with already committed sample
data. The sample record is ONLY sample completion, never an IRQ/sleep/guard
receipt. Its double-snapshot decoder cannot prove terminal success. In an actual
future profile terminal status must have separate image-bound qualification;
no host may infer sleep from the sample complete bit. The terminal callback
itself is assumed trustworthy in this offline model; another callback can still
hang/trap and prevent final checking. MSR state can change after a check through
hardware exceptions/reset; no full exclusion proof. No runtime hook was added.

MicroBlaze object compile PASS, model frame88 (previous84), excludes capture/
callbacks/caller. New source changes compiler flow: prior word-v2 linked profile
and manifest are HISTORICAL/STALE, not silently rehashed. Full changed target
link/flow qualification remains next work before any new audit receipt.

## Initialization findings

Reviewed actual previous word-v2 XPfw_Init at ffdc0050 loads SP=ffddd6a0,
sets stack high/low and clears __bss_start..__bss_end with swi and increment4
before calling XPfw_Main. Stack/BSS symbols are word-aligned. Source and linked
bytes agree; this supports conditional stack/BSS setup IF this entry executes.
It does not establish live vector mapping, actual reset path, no later stack
corruption, exception/ROM stack use or fresh session uniqueness. Initializing
BSS after reset can erase the one-shot state; it cannot guarantee nonce lifetime.
No new PMU RAM write or stack policy change occurred.

No HW/JTAG/UART/network/reset/register access. Physical recovery, PMU-to-AP0
visibility, actual terminal entry status and callback behavior remain OPEN.
MUST NOT DEPLOY; DDR NOT_ADMITTED. Next safe offline work: rebuild changed
profile and verify the final MSR call dominates terminal adapter entry; test
that a committed sample alone cannot become a terminal receipt.
