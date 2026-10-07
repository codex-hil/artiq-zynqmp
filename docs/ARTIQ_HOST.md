# ARTIQ host CLI environment

Installed separately from the gateware/archaeology Python venv:
`/srv/codex-hil-data/artiq-zynqmp/venvs/artiq-host` (Python 3.12).
Shared launchers in `/home/codex-hil/.local/bin`:
`artiq_compile`, `artiq_run`, `artiq_coremgmt`, `artiq-host`.
This provides experiment compilation and host CLI tools. Dashboard/Qt and
master deployment are outside this installation's verified scope.

Sources copied to separate build checkouts before pip installation, leaving
reference checkouts unchanged:

- ARTIQ: `486e8f897547d282d46a02c30463449c21e30cfe`, installed version
  `10.0+unknown.beta` from that development snapshot.
- sipyco: `75f055c2ee29c09a49912e63ed49c7b7cae953c4` (1.14).
- NAC3: `322b7bd2537e176d7997f816ae2fb6ab9e029939`, the same LLVM19 compiler
  already verified in QEMU and on A53 CPU1. Not latest NAC3 HEAD.

NAC3 module was reused from
`build/abi-acceptance/kernel-abi/compiler/release/libnac3artiq.so` and copied
to the host venv's site-packages as `nac3artiq.so`, as a native Python extension.
It requires libLLVM.so.19.1 and its dependencies; imports passed on this host.
Other dependencies are frozen in `requirements-artiq-host.txt`.

## Use

```sh
artiq_coremgmt -D 192.168.2.16 log
artiq-host python -c 'import artiq, nac3artiq; print(artiq.__version__)'
```

Update the DHCP address when needed. Offline compilation from this repository:

```sh
mkdir -p /large-disk/compile-check
artiq_compile --device-db examples/device_db_genesys.py \
  --dataset-db /large-disk/compile-check/datasets.mdb \
  -o /large-disk/compile-check/genesys_ttl.elf \
  -d /large-disk/compile-check/genesys_ttl_debug.elf examples/genesys_ttl.py
```

The experiment compiles to ARM32 ELF using Cortex-A9 target, matching the
A53 AArch32 execution proof. Its 125 mu pulse corresponds to 1 us at the
local-RTIO 8 ns reference period. The compiled artifact is 2620 bytes.
Compilation does not run the experiment or switch physical TTL.
The new two-core kernel-bringup firmware executes the separate no-output
`examples/genesys_network_probe.py` through normal artiq_run and scalar RPC.
Build/start instructions: boards/genesys_zu-5ev/3_kernel/README.md.
The TTL experiment still cannot load (rtio_output is intentionally unresolved);
physical TTL, DMA and complete exception/RPC support remain pending.
No physical experiment was attempted during this installation.

## Recreate on this host or another host

1. Clone the pinned ARTIQ/sipyco into disposable build checkouts.
2. Create a Python 3.12 venv on a disk with space. On this host ensurepip was
   absent: `python3 -m venv --without-pip VENV` followed by the existing project
   pip's `python -m pip --python VENV/bin/python install pip` bootstraps it
   without installing system packages.
3. Install `requirements-artiq-host.txt` into that venv, then
   `pip install --no-build-isolation --no-deps ARTIQ_CHECKOUT SIPYCO_CHECKOUT`.
4. Rebuild the pinned NAC3 following `prototypes/kernel-abi/README.md`, or use
   the preserved matching native module. Copy it as `nac3artiq.so` into the
   new venv site-packages; install matching LLVM19 runtime dependencies.
5. Check NAC3 import, the three CLI `--help`, `pip check`, offline compilation,
   and management with the actual board IP. Do not use a random PyPI ARTIQ or
   replace the compiler without repeating ABI validation.

Validation and artifact hashes:
`evidence/artiq-host-install-2026-10-07.json`. Large installation logs and
compiled artifacts: `/srv/codex-hil-data/artiq-zynqmp/build/artiq-host-check`
and `build/artiq-host-install.log`.
