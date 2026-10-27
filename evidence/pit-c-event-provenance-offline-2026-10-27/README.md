# Fake-C callback event trace -> derived receipt crosscheck — offline

45 PIT tests PASS. Existing real C lifecycle/status fixture optionally emits
five188-byte event frames: separate MSR callback observations, operation return
flags, lifecycle/publication results, post-publication fake MSR, sample bytes and
receipt bytes. Without PIT_EVENT_TRACE the original fixture wire format remains
unchanged and its previous tests still PASS. No production/target source changed.

Both optimized and ASan/UBSan runs: staged Python producer independently derives
status and SHA256 fields from C-produced observations/sample bytes plus supplied
image bytes. Its96receipt bytes equal actual C publisher bytes for all five cases:
COMPLETE, READ_FAILED/no sample, PUBLICATION_UNKNOWN/committed sample, late IRQ
before final check, and IRQ drift after final snapshot during receipt writing.
Final case explicitly distinguishes recorded MSR from later fake actual MSR;
valid record remains intent, never current IRQ or sleep residency proof.

12 trace/header/MSR/sample/receipt byte mutations plus wrong image and truncation
are rejected. C fixture uses precomputed digest of its fixed fake image/sample
vectors; Python independently recomputes both over corresponding bytes. This is
cross-language consistency, NOT target-side SHA256, authenticated execution,
image boot identity or trusted hardware trace. All inputs are fake/synthetic.
Raw synthetic trace preserved as hex with SHA256; no physical capture involved.

No JTAG/UART/network/reset/register/HW access. No target image/backend/manifest
change. MUST NOT DEPLOY; DDR NOT_ADMITTED. Next safe offline work: expand this
cross-language trace to initial MSR/disable failures and post-callback read error,
ensuring absent observations cannot become fabricated MSR/sample success.
Physical metadata production, independent hung-read recovery and AP0 visibility
remain OPEN and cannot be waived by this software consistency result.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
