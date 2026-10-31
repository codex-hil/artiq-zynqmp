# Conditional normal-path stack model — offline 2026-10-31

LGPL-3.0-or-later. No hardware operations, firmware or frozen-profile change.

Read-only model first requires exact digest-root function/storage/SHA-constant
profile. It traverses direct brlid targets from reviewed listings and substitutes
explicit manually reviewed callback-register bindings for indirect brald sites.
Missing bindings/functions, changed prologue allocation, recursion or missing
frame entries reject. All28 reachable functions have reviewed static frames;
allocation instructions match those frames in the exact image. Sequential calls
use maximum nested depth, not a sum across separate calls. Loops do not add frames.

Conditional normal-path peak792 bytes: root336 + capture156 + SHA300 + swap0.
Call sites, graph and frames in report.json include observer/disable/ordered-read/
raw-MMIO/sample-publisher/receipt-publisher/slot-fence paths. This extends the
scoped SHA subtotal to a modeled normal-path maximum under the listed callback
assumptions. It is NOT a whole-stack/exception bound or generic instruction/CFG
proof: bindings are reviewed assumptions, not arbitrary callback dataflow solving.
Indirect callback substitution, concurrency, hostile pointer/stack mutation and
execution outside listed call shapes are excluded premises.

No bound on incoming caller frames, asynchronous IRQ/NMI/debug/error/exception
frames, exception handlers, hardware faults, stack ownership or arbitrary hung
MMIO is established. Clearing IE does not exclude those paths. Sleep intent and
a digest do not admit external PMU RAM reads or guarantee recovery. This model
must not be used as deployment permission or an automatic live stack-margin claim.

Tests check exact fixture peak/path28-node graph; missing indirect binding and
changed frame reject; graph recurrence/missing/negative frames reject; sequential
calls are modeled with maximum rather than sum. Existing image remains unchanged;
new model has its own recorded source/artifact hashes and does not alter frozen
inventory or claim that old gate now admits execution.

Next safe offline step: inventory exception/NMI/debug/error vector entry and
handler dependencies in this exact ELF, identify frames/calls not covered by this
normal-path model and record concrete unbounded paths. No physical exception
injection or changes to vector/IRQ policy without a separately admitted plan.
Entry protocol/image-input trust/no-wake reader lifetime/recovery remain open.

Coverage correction found by new tests: the previous29-function gate did not
include fence, despite that function being reachable through slot barrier.
The separate stack audit adds exact fence range/body/listing pins and six word
mutation controls. Its requirement is stronger than the old frozen gate; that
frozen inventory is not changed or retroactively described as covering fence.
First full test run exposed the missing synthetic fixture fence (136 tests,
1 failure/1 error). Fixed fixture plus additional independent fence pins; actual
ELF and conditional peak remain unchanged. No hardware claim or gate relaxation.

Final full PIT suite:137 tests PASS.
