# RO adapter wired into target audit context — offline

56 PIT tests PASS. Returning composition accepts an optional separate caller-owned
zero-initialized RO adapter; raw read/context are bound at prepare before any
callback. Failed prepare rejects whole plan before consumption/callbacks. Host
model's null-adapter path remains for historical generic tests. Actual target
audit entry now REQUIRES nonnull adapter; otherwise it enters terminal without
attempting capture. No physical storage/session/lease is established by pointer.

New optimized+ASan/UBSan context fixture uses the composition's own adapter
wiring (not a fixture read shim): successful eight reads, all eight raw error
positions and a pre-armed adapter rejected before raw calls. Nine emitted
sample/receipt pairs pass Python validation, errors have zero sample writes.
Original external-shim address/budget tests remain separate and still PASS.
Underlying callback remains injected/fake; this is NOT Xil_In32 integration.

Fresh full PMU link/layout/no undefined symbols PASS. Entry and five forwarding
functions pass no-subword-store checks. Frame292 entry/read52 =>344largest
internal entry+forwarder, excluding raw callback/caller/exception stack. RO logic
is inlined into read_word; both guarded and null-adapter host-model branches
exist in that function. Audit entry's nonnull check is not a full symbolic
proof against hostile callbacks/state mutation. Prepare/budget/sequence state
is not tamper-resistant, thread-safe or reset-persistent identity.

Plan C layout changed: archived source/ELF/helper addresses and old gate pins
remain historical, not silently rehashed. Prior composition flow checker
explicitly refuses this new compiler shape. No updated deployment/admission
manifest created. Real MMIO callback still absent; zero return means a word
returned, not a bus-fault diagnosis or bounded time. Hash provenance, independent
hung-read recovery and actual sleep/AP0visibility remain OPEN.

No hardware/JTAG/UART/network/reset/register access. MUST NOT DEPLOY; DDR
NOT_ADMITTED. Next safe offline work: qualify the new read_word branch/control
shape and exact RO address/count/state checks with consistent ELF mutations
before extending any read-only audit gate. No physical attempt selected.
