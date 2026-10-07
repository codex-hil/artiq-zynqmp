#!/usr/bin/env bash
# Host orchestrator: Rust open-source toolchain, AMD BSP only inside shared Vivado.
set -euo pipefail
if [ "$#" -ne 4 ] && { [ "$#" -ne 5 ] || [ "$5" != "--kernel" ]; }; then
    echo "Usage: $0 SYSTEM_TOP_DTS CSR_MAP OUTPUT ARM_GNU_PREFIX [--kernel]" >&2
    exit 2
fi
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
sdt=$(realpath "$1")
csr=$(realpath "$2")
out=$(realpath -m "$3")
arm=$(realpath "$4")
if [ -e "$out" ]; then echo "Use a fresh output directory: $out" >&2; exit 2; fi
mkdir -p "$out"
export TMPDIR=${TMPDIR:-/srv/codex-hil-data/toolchains/amd/shared/tmp}
cargo test --locked --lib --manifest-path "$repo/boards/genesys_zu-5ev/2_firmware_a53/Cargo.toml" --target-dir "$out/rust"
cargo build --locked --release --target aarch64-unknown-none --manifest-path "$repo/boards/genesys_zu-5ev/2_firmware_a53/Cargo.toml" --target-dir "$out/rust"
lib="$out/rust/aarch64-unknown-none/release/libgenesys_artiq_services.a"
vivado-container shell "$repo/scripts/build_ethernet_firmware.sh" "$sdt" "$out/amd" "$arm"
attach=(--app "$out/amd/app" --staticlib "$lib" --csr-map "$csr")
if [ "$#" -eq 5 ]; then attach+=(--kernel); fi
python3 "$repo/scripts/attach_a53_services.py" "${attach[@]}"
vivado-container shell -c '
set -eu
amd=${AMD_ROOT:-/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2}
export PATH="$1/bin:$amd/tps/lnx64/cmake-3.24.2/bin:$PATH"
exec "$amd/Vivado/bin/empyro" build_app -w "$2"
' build "$arm" "$out/amd/app"
sha256sum "$sdt" "$csr" "$lib" "$out/amd/app/build/lwip_echo_server.elf" > "$out/artifacts.sha256"
