> 2026-10-27 correction: separately linked array copies contain byte stores,
> unsuitable for PMU word-write-only RAM. See `../pit-pmu-word-write-fix-offline-2026-10-27`.
> Raw artifacts unchanged; this does not imply the full inlined profile had byte stores.

# C PIT collector — offline, no hardware backend

Nine Python test cases PASS, including actual C compiled at -O2 and at -O1
with ASan/UBSan. The C fixture checks success, all eight callback failure
positions, rejected reentrancy/duplicates/invalid entries and a 64-bit nonce.
Failed collection leaves the output unchanged. Staged values are initialized,
then copied only after eight successful callbacks; completion is written last
in C source. This is single-context source-level publication, not a qualified
cross-core/barrier protocol. The caller must not expose the result until return.
State/result must be separate owned initialized storage; hostile callbacks,
concurrent execution, resets and external observers are outside this contract.

MicroBlaze v9.2 little-endian -Os object: text548/data0/bss0; static frame88
bytes EXCLUDES callback/caller/library stack. mb-nm shows unresolved memset
from staged-array initialization. Object/disassembly retained; no final LTO
link or target execution. This is not a complete stack/dependency audit.
Object SHA256: 6ed8eb3c700c338267dc9e274a4da940df427733b5834842d884b50176a652fa
Compiler flags: -std=c11 -Wall -Wextra -Werror -mlittle-endian
-mxl-barrel-shift -mxl-pattern-compare -mxl-reorder -mxl-soft-mul -mxl-soft-div
-mcpu=v9.2 -Os -fstack-usage -c.

No MMIO implementation, register access, firmware integration, deployment,
reset or hardware test occurred. A returned callback error stops collection;
a hung callback remains uninterruptible. Eight calls do not bound elapsed time.
No DDR admission follows. Next safe offline work: final target link/ABI and
publication-path review, including memset and total callback stack obligations,
before designing any physical adapter or new admission manifest.

Reproduce: python -m unittest discover -s tests -p 'test_pit*.py' -v.
