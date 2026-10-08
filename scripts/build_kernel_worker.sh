#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 3 ]; then echo "Usage: $0 ABI_TOOLS OUTPUT CSR_MAP" >&2; exit 2; fi
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
tools=$(realpath "$1")
out=$(realpath -m "$2")
csr=$(realpath "$3")
mkdir -p "$out"
export TMPDIR=${TMPDIR:-/srv/codex-hil-data/toolchains/amd/shared/tmp}
export PATH="$tools/root/usr/bin:$tools/root/usr/lib/llvm-19/bin:$PATH"
export LD_LIBRARY_PATH="$tools/root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CARGO_TARGET_ARMV7_UNKNOWN_LINUX_GNUEABIHF_RUSTFLAGS='-C target-cpu=cortex-a9 -C relocation-model=static -C force-unwind-tables=yes'
python3 - "$csr" "$out/rtio_csr.h" <<'PY'
import json,sys
from pathlib import Path
m=json.loads(Path(sys.argv[1]).read_text())
if m['csr_base']!=0xa0000000 or m['csr_data_width']!=32:raise ValueError('Unexpected CSR ABI')
Path(sys.argv[2]).write_text(''.join(f"#define {k.upper()} 0x{v['address']:X}UL\n" for k,v in m['registers'].items()) + ''.join(f"#define {k.upper()}_WORDS {v['words']}UL\n" for k,v in m['registers'].items()))
PY
cargo +1.87.0 build --locked --release --target armv7-unknown-linux-gnueabihf --manifest-path "$repo/boards/genesys_zu-5ev/3_kernel/Cargo.toml" --target-dir "$out/rust"
source_dir="$repo/boards/genesys_zu-5ev/3_kernel/c"
clang --target=aarch64-none-elf -fuse-ld=lld -nostdlib -Wl,-T,"$source_dir/link64.ld" "$source_dir/start64.S" -o "$out/start64.elf"
arm-linux-gnueabihf-gcc -nostdlib -static -no-pie -mcpu=cortex-a9 -marm -mfpu=neon -mfloat-abi=hard -ffreestanding -fno-builtin -O2 -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0 -Wno-format -funwind-tables -I"$out" -I"$repo/boards/genesys_zu-5ev/3_kernel/include" -Wl,--gc-sections -Wl,-T,"$source_dir/link32.ld" "$source_dir/start32.S" "$source_dir/support.c" "$source_dir/printf.c" "$out/rust/armv7-unknown-linux-gnueabihf/release/libgenesys_kernel_worker.a" -lgcc -o "$out/worker32.elf"
sha256sum "$csr" "$out/start64.elf" "$out/worker32.elf" > "$out/artifacts.sha256"
