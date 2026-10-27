# C callback-return/validity-to-record metadata construction — offline

47 PIT tests PASS. New C builder derives valid MSR observations from called-mask
and zero callback return, not raw output values; derives status from initial IRQ
transition, sample operation result and final valid/equal MSR. Failed output is
ignored and unknown fields written as zero placeholders only with UNPROVEN status.
No caller terminal-success field is accepted. Image/sample hashes remain explicit
EXTERNAL inputs; builder neither computes them nor authenticates observations.

Existing six fake-C callback cases now use the real builder instead of manually
assigning record status/MSR fields. Optimized+ASan/UBSan outputs still exactly
match the independent Python producer. New C validation fixture checks high64nonce,
late IRQ/error downgrade, eight invalid-input variants preserving all output
bytes, and nulls. Called masks must be0/1/3/7; no absent-before/final-only sequence.
Sample absence/presence and status consistency enforced; hashes must be nonzero
when supplied. Input/output must be separate aligned caller-owned storage.

Actual MicroBlaze non-LTO standalone link PASS/no undefined symbols/no subword
stores,15word-store sites, frame24 excluding caller. Text at zero, MUST NOT DEPLOY.
No integration with production PMU request/main or new physical callback/backend.
Target status audit wrapper still lacks this constructor/actual callback logging;
this turn qualifies component behavior, not that full target composition.

No hardware/register/JTAG/UART/network/reset access. DDR NOT_ADMITTED. Next safe
offline work: integrate the builder into target audit composition with explicit
logging of callback return/value rather than caller-provided MSR record fields;
review resulting word stores/stack/source binding. Target hash provenance,
independent hung-read recovery and PMU-to-AP0 visibility remain OPEN.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
