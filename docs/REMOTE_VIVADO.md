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


The offline local-RTIO checker is:

```sh
python3 scripts/check_remote_rtio_build.py \
  --build /path/to/retrieved-job \
  --inputs evidence/dell-vivado-2026-10-21/inputs.json \
  --output /path/to/fresh-build-report.json
```

It requires zero Vivado exit status, unchanged pinned inputs, a new nonempty
bitstream, setup/hold/pulse-width closure, no unclocked or unconstrained internal
endpoints, complete routing and no log errors/critical warnings. The only
accepted DRC warning is the existing `RTSTAT-10`; unexpected violations require
review. Missing external input/output delays are reported explicitly, preserving
the baseline's physical I/O qualification limits. Hardware is never accessed.


## First Dell implementation and explicit IP retry

The first remote job completed with Vivado exit0, setup1.900ns, hold0.016ns,
pulse-width2.500ns, complete routing and the existing RTSTAT-10 warning only.
All28 retrieved files matched their remote SHA-256 values. The strict input
check nevertheless rejected the build: `upgrade_ip` rewrote six SD0 delay
parameters and the XCI checksum. SD0 is disabled (`PSU__SD0__PERIPHERAL__ENABLE=0`);
SD1 remains enabled and its settings did not change. This is recorded in
`evidence/dell-vivado-2026-10-21/ip-upgrade.diff`, not silently accepted.

Implementation reports are qualified separately as reports-only; the combined
input/build result remains NOT_QUALIFIED. A fresh follow-up job pins the exact
post-upgrade XCI before launching Vivado. Its directory/unit and pinned inputs
are in `evidence/dell-vivado-2026-10-21/pinned-ip-rebuild`. The same strict checker
must pass without further input mutation. No qualified hardware profile or
board image was replaced. Both jobs use the same shared build lock.


The pinned-IP follow-up completed successfully. All28 downloaded files match
remote hashes and all16 pinned inputs remain unchanged. Strict build PASS:
setup1.900ns, hold0.016ns, pulse-width2.500ns; no internal unconstrained endpoints,
complete routing, known RTSTAT-10 warning only. Evidence and exact bitstream
hash are in `pinned-ip-rebuild/build-check.json`. Physical qualification is
separate; see [candidate JTAG plan](CANDIDATE_JTAG.md).
