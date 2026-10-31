# IRQ helper configuration dependency — offline 2026-10-31

LGPL-3.0-or-later. No hardware operations.

The actual linked IRQ ELF contains XMicroblaze_ConfigTable at ffdd8b68, size
0x138. UseMsrInstr is u32 at offset44, address ffdd8b94: the linked helper's
read address. Target compiler static assertions confirm field offset/table size
using actual SDT BSP flags. Generated xmicroblaze_g.c initializer has value1;
ELF bytes at the field are 01 00 00 00. Thus the initial image, if loaded as
reviewed and unchanged, would select msrclr r0,2. This is NOT a live observation.

BSP xil_exception.c initializes static CfgPtr with XGet_CpuCfgPtr(); the macro
returns &XMicroblaze_ConfigTable. LTO emits a direct load of the field in the
reviewed helper. Table is non-const data; its immutability is not established.
A lexical reference inventory covers 397 project PIT/standalone BSP C/H/S files
and finds 20 named references. This inventory is NOT a complete writer search:
alias stores, assembly, runtime vendor code, DMA/debug corruption and exceptions
are not excluded. No live pointer/flag or executed startup claim is made.

New read-only checker checks exact table range and initial field value on ELF;
it does not change or extend the frozen instruction gate. 115 Python tests PASS,
including altered field values/ranges/duplicate symbols and false live/no-write
claims. Source hashes and target compile command are in review.json. Source text
is local BSP input, not an independent build provenance or reproducibility proof.

Next safe offline work: specify digest production for the actual sample record
and image identity. Current composition accepts caller-supplied image/sample
hashes and does not establish their origin or correlation to collected bytes.
Review ordering and canonical hashed bytes before implementing a separate profile.
No deployment, PMU RAM reader, request hook, exception exclusion, no-wake lifetime
or arbitrary-hang recovery is admitted by this dependency review.
