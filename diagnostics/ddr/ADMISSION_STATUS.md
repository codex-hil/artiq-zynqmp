# DDR write-test admission — 2026-10-23

**Not admitted.** Local ARTIQ runs successfully; a full DDR capacity/integrity
sweep has not run. This table consolidates existing evidence and does not itself
change hardware policy. Paths and hashes are in
[`review.json`](../../evidence/ddr-admission-review-2026-10-23/review.json).

| Requirement | Evidence | Remaining limitation |
|---|---|---|
| Geometry/training | Physical SPD CRC checked; controller geometry agrees; Piotr/AMD FSBL training retained | Geometry is not an integrity/capacity sweep |
| OCM execution | Physical trained EL3 observer and deliberate BRK capture passed; sampled M/C/I clear | Not a DDR writer; asynchronous SError not tested |
| Secondary A53 | Same-boot reset controls `0x300e`: CPU1–3 reset, CPU2–3 POR | Two samples do not exclude later PMU reset release |
| R5 | NCPUHALT=0; reset released; source PMU sleep sequence explains a possible state | No positive future-execution/cache exclusion |
| ZDMA/CSU | All 16 ZDMA STS/CTRL2 and both CSU STS zero in trained boot | Momentary fields do not establish exclusive ownership |
| GEM/SD/QSPI | Trained boot: GEM RX/TX off; SD transfer fields and QSPI DMA status zero | Other owners/reset epochs still unresolved |
| PL HP0 DMA | Physical runtime workload completed; 128 nonzero observations, peak27, final zero/error-free | Different boot from trained OCM capture; monitor reset loses history; epoch qualification remains0 |
| PMU | Linked IPI/hardware/slave wake capability audited | AP0 read of private0xffd40024 failed; no direct values obtained, no retry/force access |
| PCAP | FPGA programming/restoration works | CSU DMA idle is not a PCAP controller activity/ownership proof |
| Restore | Normal baseline at192.168.2.3, TTL/CoreDMA/analyzer/MonInj/Ethernet passed after latest cycle | Restoration ends the diagnostic ownership window |

## Three gaps to resolve

1. **PMU authority:** inspect maintained AMD diagnostic build options and effective
   request/event paths. Prefer an explicit, reviewed diagnostic configuration or
   telemetry from PMU's own address space over guessed AP0 aliases. Do not stop PMU,
   mask arbitrary interrupts, or treat missing network symbols as no DDR access.
2. **PL/PS reset epoch:** establish the PL image identity and a reviewed transaction
   owner/reset sequence in the same trained boot. A fresh zero counter, independent
   PL reset or DMA IDLE cannot erase outstanding PS transactions. The observer
   currently cannot arm qualification and remains diagnostic only.
3. **PCAP:** review AMD controller status definitions and non-clearing reads;
   distinguish controller activity from CSU source/destination DMA status. Avoid
   reprogramming PL or clearing status merely to obtain a quiet observation.

## Next bounded work

Review PMU configuration/telemetry options and PCAP status sources offline. Add
only new justified observations to the trained-boot lifecycle. Preserve the
existing physical failures and avoid rerunning unchanged captures. Any future
DDR writer needs a separate, explicit admission with all owners, exact boot/image
bindings, tested intervals, exception policy and mandatory restoration accounted
for. Keep the low/high DDR windows separate; never sweep the MMIO gap.

The successful short active-DMA cycle is in
[`dma-observer-short-hardware-2026-10-23`](../../evidence/dma-observer-short-hardware-2026-10-23/).
The failed long workload and failed PMU access remain independent failure evidence.
