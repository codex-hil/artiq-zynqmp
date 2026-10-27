# One-shot PIT collection contract — offline

Eight unittest cases PASS, including 40 read-failure variants (eight positions,
five exception/invalid-value cases), reentrancy and duplicate rejection. The
collector consumes its attempt before the first callback, calls only the four
RO counter addresses in two rounds, stops on the first failure, and publishes
no partial record. Invalid entry parameters do not consume the attempt.
No hardware, MMIO transport, image build or runtime change occurred.

This Python collector is a callback model, not firmware or an authenticated
capture. Its one-shot flag is not a cross-thread lock. A callback that blocks
cannot be interrupted; the eight-call bound is not a wall-clock bound. Returned
exceptions model a transport error; they do not show that Xil_In32 can return
one. Completion proves only callback completion, never elapsed ticks or DDR
exclusivity. All outputs keep physical_backend_ready/destructive_test_allowed false.

## PMU-local capture design, not admitted

A future separate C collector should use the same fixed address order, stage
all eight u32 words privately, and commit version/nonce/completion only after
the final successful return. Abort/fault must leave completion invalid; no
retry, timer configuration or write-only register read is permitted. The
compiler's actual load/store and publication barriers need linked-code review.
No host DAP shortcut is proposed for PMU-local-only timer registers.

Outstanding before physical integration: exact PMU-local access/fault behavior,
bounded transport or independent recovery for a stalled read, publication and
exception paths, target linkage/stack, new source/artifact admission pins and
full normal-runtime restoration plan under the shared Genesys lease. The
current PIT samples cannot provide a qualified deadline for their own reads.
Next safe work: implement and fault-test the separate C callback collector
without MMIO, then inspect its target code. Destructive DDR remains NOT_ADMITTED.

Reproduce: `python -m unittest discover -s tests -p 'test_pit_counter*.py' -v`.
