# Correction: write-only PMU state cannot be inferred from readback — 2026-10-27

Official UG1087rev1.11 GPO0 register atffd40010 and every field including
DEBUG_REMAP are WRITE-ONLY. Thus earlier recorded readword0 does not establish
ROM/RAM selection, prescaler values or fault-tolerance policy. Prior claim of
physically confirmed default ROM mapping is RETRACTED; mapping UNKNOWN.
Raw capture, image hashes, actual guard/restore success and prior failures remain
unchanged. The invalid diagnostic inference is corrected, not historical bytes.
Source that was missing from the earlier register-header-only analysis:
https://docs.amd.com/r/en-US/ug1087-zynq-ultrascale-registers/GPO0-PMU_IOMODULE-Register?contentId=n1lYCViMc_vfwdPAscq~iA
https://docs.amd.com/r/en-US/ug1087-zynq-ultrascale-registers/PMU_IOMODULE-Module?contentId=_NJPN5dISikJ03I_ytaZcw

Safety changes: vector-v1 deployment preflight now rejects explicitly even with
fresh hashes; builder rejects --vector-snapshot before staging; MicroBlaze header
#error rejects direct opt-in compilation. Historical parser retains raw word under
raw_word_from_write_only_address with mapping UNKNOWN, not ram_vector_remap.
No new GPO read/profile permitted, no writes/remap or hardware access this turn.
Tests PASS for rebound manifest refusal, blocked builder with no output creation,
legacy transport and archival parser UNKNOWN; former exact load checks remain
only historical opcode checks, not a valid register-state diagnostic.

PIT ownership: exact source uses PIT1 for10ms scheduler; IRQ slots0/2/3 have null
handlers, which does not establish free resources because ROM/hooks remain.
UG1085p120/121 describes PMU-local four32bit PITs; SysOsc/prescale relationship
must be qualified rather than using CPU frequency blindly. UG1087 declares all
PRELOAD registers WO, COUNTER registers RO; CONTROL is mixed and needs per-field
review. Proposed preload/GPO configuration readback plan is therefore discarded.

A valid preliminary counter-only plan is included: two rounds of four RO counter
addresses, PMU-local only, no GPO/preload/control access or timer writes. No driver
or executable physical snapshot is integrated yet. Counter change does not prove
frequency, enable state, free ownership, missed wraps or monotonic64bit time.
Next offline qualify counter observation schema and rollover assumptions before
any firmware candidate. Backend physical readiness and DDR admission remain false.
Current normal runtime unchanged; no new health check.
