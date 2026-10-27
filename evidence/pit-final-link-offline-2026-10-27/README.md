# PMU collector final link review — offline

Actual PMU compiler/BSP recipe with LTO links successfully; no undefined symbols.
Collector retained with -u,pit_collect, no runtime call hook or physical callback.
Historical vendor/guard objects reused read-only for layout context: this includes
the now-prohibited vector-v1 guard, so this ELF MUST NOT be deployed. Its existence
is no exception to the write-only correction or deployment refusal.

Linked pit_collect ffdcf2b4..ffdcf4d4 has an 88-byte frame. memset resolves at
ffdd20f4, uses no stack adjustment/call in this linked body. Initialization
calls it before entry checks; invalid entry is therefore not a no-library-call
path, although it performs no user callback or output write. Callback/caller
stack and exception/reset paths remain unknown, hence no total stack bound.

ABI: incoming r5/r6 attempt/output, r7/r8 nonce, r9 callback, r10 context.
The callback is preserved in r24 and context r25. Indirect brald r15,r24 at
ffdcf36c passes context r5 (delay slot), calculated fixed counter address r6,
and private stack sample pointer r7. Address uses 0xffd40044+(index&3)*16;
eight iterations, any nonzero return takes INCOMPLETE. No MMIO load is present
in this collector: all physical transport behavior remains outside the component.

Output stores are after the successful loop, including 32 individual byte stores
for sample data. Final complete=1 is swi r4,r19,0 at ffdcf498 after the final
sample byte. No mbar exists in the collector. This supports only the documented
single-context caller-after-return contract. It does not qualify DAP/cross-core
publication, atomicity, concurrent execution or hardware visibility. No target
execution or hardware action occurred. Next safe offline task: define a separate
publication adapter with explicit visibility/commit rules and negative tests;
retain the generic collector's limited scope. DDR remains NOT_ADMITTED.
