# Strict RO adapter + returning status composition — offline

55 PIT tests PASS. Actual C RO adapter, forwarding/capture/lifecycle/builder/
receipt publisher composed through fake callbacks, optimized+ASan/UBSan. Eleven
cases: successful eight reads; transport error at each of eight positions;
forbidden GPO0 address before raw transport; pre-exhausted adapter budget before
composition. All errors yield READ_FAILED, no sample writes, and a separate
committed error-status receipt. Python decoder checks all eleven actual C outputs.

Raw callback sees exactly expected addresses; nested RO entry rejects without
extra transport. No ninth read, retry, reprepare or whole-plan reuse reaches raw
transport. Failed transport output never becomes sample data. Fake pre-exhaustion
reads are deliberately outside the model only to simulate invalid prior use; no
claim of allowed physical reads before IRQ/session/lease admission follows.

The new fixture reuses existing fake callback code; actual implementation under
test is unchanged. Source pins include both fixtures/eight C components. No
production/target source or gated image changed; wiring exists in host fixture,
not yet a qualified target entry or hardware manifest. Hashes remain fixed fake
vectors, not a target SHA256/identity implementation. No wall-time bound or hung
read recovery is proved by eight returning callback attempts.

No HW/JTAG/UART/network/reset/register access. MUST NOT DEPLOY; DDR NOT_ADMITTED.
Next safe offline work: explicit target audit wiring of the RO adapter/session
context, with aligned word-storage and linked callback/stack checks. Keep physical
MMIO transport absent until recovery and AP0 visibility qualification is concrete.
Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
