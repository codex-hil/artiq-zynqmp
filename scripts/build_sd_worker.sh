#!/usr/bin/env bash
# Embed the verified ARM worker in one CPU1 ELF: no extra FSBL handoff entry.
set -euo pipefail
if [ "$#" -ne 3 ]; then echo "Usage: $0 ABI_TOOLS WORKER32_ELF OUTPUT" >&2; exit 2; fi
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
tools=$(realpath "$1")
worker=$(realpath "$2")
out=$(realpath -m "$3")
mkdir -p "$out"
export PATH="$tools/root/usr/bin:$tools/root/usr/lib/llvm-19/bin:$PATH"
export LD_LIBRARY_PATH="$tools/root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
arm-linux-gnueabihf-objcopy -O binary "$worker" "$out/worker32.bin"
# Keep Piotr's current verified EL3 -> EL1 bridge; clear cold DDR mailbox
# only here, never in the exception-recovery path.
python3 - "$repo" "$out" <<'PY'
from pathlib import Path
import sys
repo,out=map(Path,sys.argv[1:])
source=(repo/'boards/genesys_zu-5ev/3_kernel/c/start64.S').read_text()
source=source.replace('    msr cptr_el3, xzr', '''    ldr x1, =0x200ff000
    mov x2, #0x1200
clear_mailbox:
    str xzr, [x1], #8
    subs x2, x2, #8
    b.ne clear_mailbox
    dsb sy
    msr cptr_el3, xzr''')
if 'clear_mailbox:' not in source: raise ValueError('Bridge insertion point changed')
source+='\n.section .worker,"a"\n.incbin "worker32.bin"\n'
(out/'sd_start64.S').write_text(source)
(out/'sd_link64.ld').write_text('''ENTRY(_start)
PHDRS { bridge PT_LOAD FLAGS(5); worker PT_LOAD FLAGS(5); }
SECTIONS {
 . = 0x20000000;
 .text : { KEEP(*(.text.start)) *(.text*) } :bridge
 ASSERT(. < 0x200ff000, "bridge overlaps mailbox")
 . = 0x20200000;
 .worker : { KEEP(*(.worker)) } :worker
 ASSERT(. < 0x20400000, "worker exceeds reserved image range")
 /DISCARD/ : { *(.comment) *(.note*) }
}
''')
PY
cd "$out"
clang --target=aarch64-none-elf -fuse-ld=lld -nostdlib -Wl,-T,sd_link64.ld sd_start64.S -o worker-boot.elf
sha256sum "$worker" worker32.bin worker-boot.elf > artifacts.sha256
