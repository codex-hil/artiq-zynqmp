# Standalone Genesys ZU SD boot

Status: physical cold SD boot PASS on 2026-10-08 (one power cycle).
BootROM/FSBL loaded PL and both CPU images without JTAG setup/download.
Ethernet, management, real kernels/RPC, TTL10/10 and native exceptions PASS.
Evidence: evidence/sd-cold-boot-2026-10-08.json and accompanying UART/test logs.

Use the existing Piotr DDR/SPD FSBL port and matching PS configuration,
AMD PMU firmware, local-RTIO bitstream and current CPU0 runtime. Rebuild
CPU0 with `scripts/build_a53_services.sh ... --kernel` before packaging:
it now waits up to five seconds for CPU1 READY during startup.

```sh
bash scripts/build_sd_worker.sh ABI_TOOLS WORKER32_ELF OUTPUT_WORKER
python3 scripts/build_boot_image.py \
  --fsbl FSBL_ELF --pmufw PMU_ELF --bitstream TOP_BIT \
  --worker-boot OUTPUT_WORKER/worker-boot.elf \
  --application CPU0_ELF --output-dir OUTPUT_BOOT
bootgen -arch zynqmp -read OUTPUT_BOOT/boot.bin pht
```

CPU1 ELF contains two load segments: the verified EL3/AArch64 bridge at
0x20000000 and unchanged ARM worker binary at 0x20200000. FSBL records one
CPU1 handoff, not a separate entry for the raw ARM binary. The SD bridge
clears mailbox 0x200ff000–0x201001ff before entering EL1/AArch32. Recovery
after kernel exceptions continues to preserve the normal mailbox handshake.
CPU1 is released before the final CPU0 handoff; CPU0 waits for READY.

FSBL configures DDR/clocks/AFI using generated psu_init, loads PL, removes
PS/PL isolation and releases PL reset. Generated PL0 clock value matches
the tested JTAG configuration (0x01010c00 at 0xff5e00c0).

Prepared host image:
`/srv/codex-hil-data/artiq-zynqmp/build/sd-boot-2026-10-08/boot.bin`.
Input and output SHA-256 values are in the adjacent `artifacts.json`;
partition headers are in `partition-headers.txt`.

For physical validation, first identify the card and preserve its contents.
Copy this image as `BOOT.BIN` to a FAT32 boot partition. Do not format an
existing card or overwrite its BOOT.BIN without a backup. Insert the card
with board power off, select the documented Genesys SD boot setting, and
power-cycle: volatile alternate JTAG boot settings disappear at power loss.
Capture UART from power-on, verify PMU/FSBL/PL and CPU1 startup, DHCP,
management and genuine artiq_run. Run the loopback and exception suites.
Record cold-power-cycle repetitions separately; one cycle has passed.

No Linux, U-Boot, Vitis or PetaLinux is part of this boot image.

Select JP3 pins labeled SD with power off; insert card in J9.
Source: https://digilent.com/reference/programmable-logic/genesys-zu/reference-manual#microSD_boot_mode

After power-on the board obtained192.168.2.16 by DHCP. On this host:

```sh
artiq_coremgmt -D 192.168.2.16 log
artiq_run --device-db examples/device_db_genesys.py \
  --dataset-db /srv/codex-hil-data/artiq-zynqmp/build/sd-user-datasets.mdb \
  examples/genesys_loopback.py
```

Loopback requires the verified JB1→JB2 jumper. The current runtime remains
`kernel-bringup`; successful SD boot does not imply DMA/DRTIO completeness.
