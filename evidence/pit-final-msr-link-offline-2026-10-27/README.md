# Final-MSR v3 full target link — offline

33 PIT tests PASS. Recompiled all six current PIT sources, linked with fresh
non-vector vendor objects. Actual source/artifact/layout/word-store/scoped-flow
audit PASS:30internal branches/10abstract callback sites, exact terminal. New
profile final-msr-v3; earlier shapes rejected. New synthetic-ELF controls remove
final MSR callback, comparison or error branch while updating disassembly and
ELF consistently; all rejected. Existing adversarial C tests show committed
sample data coexisting with IRQ_UNPROVEN. No sample-to-sleep conversion added.

Linked normal-result tail: callback at ffdcf42c, callback-error test ffdcf434,
read current/reference words ffdcf438/43c, xor ffdcf440, mismatch test ffdcf444,
then status to r6 and branch ffdcf44c to adapter call ffdcf2ac. The initial
IRQ-error route ffdcf2a4 sets result1/IRQ_UNPROVEN and intentionally need not
pass the final successful-result comparison. Rejected entry goes straight to
fallback terminal. This is a pinned local instruction-block/control inventory,
NOT a general symbolic dominance/liveness proof for every possible branch,
callback, exception or hostile mutation. Callback can lie, hang or trap; no
completion of a hung MMIO instruction is guaranteed by final MSR checking.

LTO frame172, adapter4, terminal0, excluding caller/callback/exception frames.
Aligned entry SP and frame172/record offset28 preserve word alignment; no
subword stores in entry. This is conditional target review, not live stack/
initialization proof. Exact MSR policy is only represented by abstract callbacks.
There remains no vendor main/request hook, physical callback backend or bound
mailbox. Entry is retained solely for audit. The sample record's complete bit
means completed samples, never final IRQ state or actual terminal sleep.

Fresh profile audit manifest stays deployable=false; require_deployment always
refuses. Prior manifests/pins unchanged and stale for changed code. No hardware
JTAG/UART/network/reset/register action. MUST NOT DEPLOY; DDR NOT_ADMITTED.
Next safe offline work: define a separately versioned terminal-status receipt
bound to sample/session/image without treating any pre-sleep write as proof of
sleep residency; fault-injection model must keep these distinctions explicit.
Actual AP0 visibility and independent hung-read recovery remain unresolved.
