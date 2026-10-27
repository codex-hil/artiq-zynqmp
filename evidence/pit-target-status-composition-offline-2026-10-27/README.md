# Target-linked status composition — offline audit only

Fresh full PMU link PASS/no undefined symbols, footprint PASS, scoped entry
word-store checker PASS38sites/no subword stores. Seven current PIT objects
plus fresh non-vector vendor objects. Entry retained with -u only; no main/
request hook, physical callbacks, slot allocation or target execution. Terminal
remains exact mbar1/sleep/backbranch.40PITtestsPASS including controlled refusal
for missing adapter. Host composition tests do NOT execute this target wrapper.

LTO entry1132bytes/frame220; terminal0. Callback/caller/exception stack unknown.
Conditional word-aligned SP, frame220/record28 preserve alignment (-220+28=-192).
This is not all-path stack/access/visibility proof. Source status is written at
ffdcf29c -> plan+20; publication outcome at ffdcf2bc -> plan+152; terminal call
ffdcf2c0 -> ffdcf1b0. Lifecycle/publication outcomes remain separate.

Wrapper defers the returning model terminal callback until status publication,
then enters the actual nonreturning audit terminal. IMPORTANT: record MSR/hash
metadata remains caller-supplied, NOT derived from actual observation bytes or
computed hashes by this wrapper. Framing checks cannot authenticate it. This is
a call/stack analysis arrangement, NOT a trustworthy physical receipt producer.
Final-MSR snapshot still precedes publication; bytes are never current IRQ or
sleep-residency proof. No new success/admission claim follows from the link.

Different entry/layout is incompatible with v3 audit shape. First refusal test
raised KeyError for missing terminal_adapter (failed closed); checker corrected
to explicit required-symbol ValueError and regression PASS. Refreshed hashes
still yield controlled refusal. No new shape or hardware manifest admitted.
Existing manifests may be stale after checker change; no historical pins rewritten.

No HW/JTAG/UART/network/reset/register access. MUST NOT DEPLOY; DDR NOT_ADMITTED.
Next safe offline work: observation-to-receipt provenance model deriving status,
MSR and sample/image binding from actual captured bytes, with wrong/stale caller
metadata negatives. Independent MMIO recovery/AP0 visibility remain unresolved.
