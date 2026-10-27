# Strict AIB component cross-compiled for actual PMU — 2026-10-27

Offline compilation only. Replayed actual xpfw_aib.c compiler options from the
retained AMD compile_commands recipe: MicroBlazev9.2,little-endian,softmul/div,
barrel/pattern/reorder,Os,fatLTO and original BSP includes/specs. Source/output
replaced explicitly; added strict warnings and stack-usage report. Separate
-fno-lto twin provides stack report; no original source/library modified.

Both builds PASS. Object text1264bytes, data/bss0; .text byte-identical across
fatLTO and nonLTO twins (hash in audit.json). NonLTO static frames snapshot48 and
hold116bytes: internal path164 excluding callbacks, caller and library helpers.
This is NOT final linked stack bound; LTO/inlining/ABI and callback stack matter.

Compiler introduced memset(out,0,36) for result initialization. ELF symbol table
and native-text relocation identify unresolved memset. mb-nm -u on fatLTO object
printed no undefined symbols; do not interpret that as self-contained code.
NonLTO nm and readelf expose dependency. Existing PMU ELF contains a memset but
is not the final link for this component. Direct internal snapshot calls and
register-indirect callbacks remain; no physical callback address is bound.

All reports/build commands and artifact hashes retained. No linked firmware,
MMIO backend, device access or AIB writes. Initialized result memory must be in
reviewed local caller storage; bss0 does not prove no DDR access. Current runtime
unchanged and not rechecked. DDR NOT_ADMITTED.

Next offline: add boot/nonce/sequence binding around the callback protocol and
qualify stale/mismatched/duplicate execution against actual C; then isolated final
PMU link/footprint audit before any backend or deployment selection.
