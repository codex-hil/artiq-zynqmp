# Lifecycle status -> terminal-intent writer coupling — offline real-C test

39 PIT tests PASS. New fixture links unchanged actual collector, publisher,
capture, lifecycle and terminal-record C components with fake MSR/read/write/
barrier callbacks. Both -O2 and ASan/UBSan executions PASS: five complete scenarios
and54terminal-publication interruptions (27positions x before/after effect).
The terminal fixture returns; no PMU sleep, physical target or firmware hook.

Five pairs of actual C-produced sample/terminal bytes are decoded by the unchanged
Python decoder: COMPLETE, READ_FAILED (no sample publication), PUBLICATION_UNKNOWN
(sample commit took effect before returned error), IRQ_UNPROVEN (read callback
re-enabled IE), and COMPLETE followed by IRQ change DURING receipt publication.
Each keeps sleep_proven/hardware/admission false. Only reported COMPLETE exposes
decoded samples; errors do not promote samples even when already committed.

The fifth scenario is an explicit LIMIT test: the status snapshot is taken before
receipt publication. That later callback can change IRQ while the bytes still
report matching earlier MSR. Valid receipt bytes cannot establish current IRQ,
actual terminal entry or sleep. Do not add another circular success claim from
those bytes. The decoder accepting this intent record while denying sleep proof
is expected. A future concrete terminal adapter requires trusted own callback
behavior and independent visibility/residency qualification; fake tests do not
satisfy these requirements.

Publication status and lifecycle result remain separate. In all54receipt failures
lifecycle can be COMPLETE while receipt publication is UNKNOWN; error-after-commit
can leave a committed terminal record. No retry/rollback is performed. The fixture
uses a precomputed digest for its one fixed sample vector, independently verified
by Python over actual C output. It is NOT a target SHA256 producer or authenticated
image/session provenance implementation. Image digest is synthetic12...12.

No production C source or target v3 manifest changed this turn. No HW/register/
JTAG/UART/network/reset access. MUST NOT DEPLOY; DDR NOT_ADMITTED. Next safe offline
work: target-linked composition audit for status-publication adapter and stack/
word-store paths, without physical callbacks or treating pre-sleep intent as proof.
Independent stuck-read recovery and PMU-to-AP0 visibility remain OPEN.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
