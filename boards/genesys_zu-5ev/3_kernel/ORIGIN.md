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
