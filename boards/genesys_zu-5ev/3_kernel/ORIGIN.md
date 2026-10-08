Continues Piotr's C BSP → Rust staticlib architecture with an A53 CPU1
AArch32 worker, using the already physically verified execution-state bridge.

src/rpc.rs and upstream-io/{lib.rs,proto.rs,cursor.rs} are unmodified copies
from m-labs/artiq-zynq @15c856f315969b5c1d01d2917ed52f1b0f199677.
LGPL-3.0-or-later; license preserved here. upstream-io Cargo template adapted
only to pin crates and remove unused Cortex-A9 board-support dependency.
ELF loader is the previously preserved upstream-dyld; no new ELF loader or
RPC value serializer was written. Board/cache/channel/startup adapters are new.

Local RTIO CSR sequencing follows src/libksupport/src/kernel/rtio_csr.rs
at the same preserved artiq-zynq revision: target clears data, LSW triggers
output; WAIT/underflow/destination and input status bits retain upstream
meaning. Board support uses generated 32-bit MiSoC CSR addresses/word counts,
not copied Cortex-A9 memory maps. Exception behavior is explicitly fail-stop
until upstream exception/unwind integration; it is not equivalent yet.

## Exception implementation

Preserved M-Labs ARM EHABI exception implementation eh_artiq.rs, libdwarf,
libunwind, llvm_libunwind/{src,include,LICENSE.TXT}, freestanding include
headers and MIT printf.c from artiq-zynq @15c856f315969b5c1d01d2917ed52f1b0f199677.
The LLVM subtree object is c987b466a0211ad682c72b1cf3d98850a85933de.
LLVM Apache2/LLVM-exceptions license and Rust MIT/Apache license texts kept;
original source notices retained. No new DWARF parser/personality/unwinder.

Board adaptations: libc retains FFI types without Cortex-A9 UART dependency;
libunwind build adds Cortex-A9 hard-float flags and drops LLVM bitcode LTO
for the GNU final linker. eh_artiq gets load address from preserved dyld's
Image, and stops at an explicit worker_invoke assembly boundary before the
polling worker. kernel.rs supplies dynamic exidx lookup and upstream-format
exception packet marshaling through volatile byte stores (CPU1 MMU-off
forbids unaligned optimized word stores). Recoverable uncaught exceptions
reset only the CPU1 polling activation/private heaps after CPU0 packet-copy
acknowledgement; PS/PL/networking remain running. Native exception algorithms
otherwise preserved; bounded packets/unsupported faults remain bring-up limits.
