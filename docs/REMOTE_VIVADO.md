# Vivado builds on Dell

New heavy FPGA builds run on `codex-hil@192.168.2.7`, using the existing
Optiplex key `~/.ssh/dell_build`. Never copy the private key. The shared
Vivado/bootgen 2025.2 launchers are under `/home/codex-hil/.local/bin`;
noninteractive SSH should use their full paths. The Dell has 64 GB RAM and
four separate NVMe work areas. Use a fresh project/job directory under
`/srv/nvme-fast-1/vivado-work` and the common build lock:

`/srv/nvme-fast-1/vivado-work/.vivado-build.lock`

Run one heavy build at a time through that lock. Keep an exit-code file and
reports; an old `.bit` file is not a successful-build proof. Do not modify a
running job directory. Do not delete the existing Optiplex installation or
installers. Full shared handoff is in `/home/codex-hil/docs/toolchains/vivado-remote-handoff.md`.

The Dell launcher uses rootless Podman and mounts the installation read-only,
`/home/codex-hil` and the four NVMe directories. Other Optiplex paths under
`/srv/codex-hil-data` are not automatically available. Python/Migen/ARTIQ/Nix
and cross-compilers were not migrated with Vivado. For now, generate HDL on
Optiplex and transfer explicitly selected HDL/XDC/IP/init inputs to Dell.
Resolve external/absolute symlinks and record all input hashes.

## Current Genesys rebuild

`evidence/dell-vivado-2026-10-21/results.json` records the exact job directory
and systemd user unit. The input manifest pins 16 transferred files from the
preserved local RTIO/CoreDMA/analyzer/MonInj HDL build. Only the Vivado maximum
thread setting changed from 2 to 8. No bitstreams/checkpoints or existing IP
synthesis results were copied as build inputs. PS IP is regenerated from XCI.
Transfer hashes were verified on the remote host before accepting the job.

The job is a systemd user service and owns the common build lock across Vivado.
It may wait behind another thread's build. From Optiplex, inspect it using the
recorded directory and unit:

```sh
ssh -i ~/.ssh/dell_build -o BatchMode=yes codex-hil@192.168.2.7 \
  'systemctl --user status JOB.service --no-pager'
ssh -i ~/.ssh/dell_build -o BatchMode=yes codex-hil@192.168.2.7 \
  'cd /srv/nvme-fast-1/vivado-work/JOB && cat state.txt && tail -30 console.log'
```

`exit.json` is written when Vivado returns. `FINISHED_CHECK_REPORTS` means
exit code zero, not qualified timing/DRC. Retrieve the logs, timing/DRC/route
reports, CSR map and bitstream to a fresh local result directory, verify hashes,
then run the project report checks. This rebuild demonstrates portability of
preserved generated inputs; fresh-source HDL provenance remains separate.

JTAG, resets, UART and all hardware tests stay on Optiplex under existing board
leases. The remote container has no USB/network hardware access. Do not copy
lock files or use the remote build lock as a board lease. Existing hw_server
containers and qualified board images remain untouched.
