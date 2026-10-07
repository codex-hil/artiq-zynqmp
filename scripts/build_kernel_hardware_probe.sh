#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 4 ]; then echo "Usage: $0 MODULE_ELF ABI_TOOLS OUTPUT CSR_MAP" >&2; exit 2; fi
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
module=$(realpath "$1")
tools=$(realpath "$2")
out=$(realpath -m "$3")
csr=$(realpath "$4")
mkdir -p "$out"
python3 - "$csr" "$out/rtio_csr.h" <<'PYTHON'
import json,sys
from pathlib import Path
mapping=json.loads(Path(sys.argv[1]).read_text())
if mapping['csr_base'] != 0xA0000000 or mapping['csr_data_width'] != 32: raise ValueError('Unexpected CSR ABI')
r=mapping['registers']
if r['rtio_counter']['words'] != 2 or r['rtio_counter_update']['words'] != 1: raise ValueError('Unexpected counter ABI')
Path(sys.argv[2]).write_text(f"#define RTIO_COUNTER 0x{r['rtio_counter']['address']:X}UL\n#define RTIO_COUNTER_UPDATE 0x{r['rtio_counter_update']['address']:X}UL\n")
PYTHON
export TMPDIR=${TMPDIR:-/srv/codex-hil-data/toolchains/amd/shared/tmp}
export PATH="$tools/root/usr/bin:$tools/root/usr/lib/llvm-19/bin:$PATH"
export LD_LIBRARY_PATH="$tools/root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export KERNEL_ELF="$module"
export CARGO_TARGET_ARMV7_UNKNOWN_LINUX_GNUEABIHF_RUSTFLAGS='-C target-cpu=cortex-a9 -C relocation-model=static'
cargo +1.87.0 build --locked --release --target armv7-unknown-linux-gnueabihf --manifest-path "$repo/prototypes/kernel-abi/baremetal/Cargo.toml" --target-dir "$out/rust"
clang --target=aarch64-none-elf -fuse-ld=lld -nostdlib -Wl,-T,"$repo/diagnostics/kernel-a53/link64.ld" "$repo/diagnostics/kernel-a53/start64.S" -o "$out/start64.elf"
sed 's/0x40200000/0x20200000/' "$repo/prototypes/kernel-abi/baremetal/link32.ld" > "$out/link32.ld"
arm-linux-gnueabihf-gcc -nostdlib -static -no-pie -mcpu=cortex-a9 -marm -mfpu=neon -mfloat-abi=hard -ffreestanding -fno-builtin -O2 -DGENESYS_HARDWARE -I"$out" -Wl,--gc-sections -Wl,-T,"$out/link32.ld" "$repo/prototypes/kernel-abi/baremetal/start32.S" "$repo/prototypes/kernel-abi/baremetal/probe.c" "$out/rust/armv7-unknown-linux-gnueabihf/release/libgenesys_aarch32_loader_probe.a" -lgcc -o "$out/probe32.elf"
sha256sum "$csr" "$module" "$out/start64.elf" "$out/probe32.elf" > "$out/artifacts.sha256"
