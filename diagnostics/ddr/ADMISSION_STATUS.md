# DDR write-test admission — 2026-10-23

2026-10-24 vector boundary: BSP hardware base is PMU ROM0xffd00000; ELF RAM
stubs at0xffdc0000 do not prove event forwarding. RAM handler/stack estimates
remain conditional. See [ROM/RAM boundary](../../evidence/pmu-rom-vector-boundary-2026-10-24/README.md).


## 2026-10-24 authoritative checkpoint

The dated rows below retain earlier checkpoints. The PMU row and old transport/
USB blockage descriptions are superseded by this checkpoint.

Physical sleep-guard capture PASS: four coherent nonce-bound records show
MSR `0x80000106 -> 0x80000104` (IE only cleared), ACK0 and unresolved0x7f.
Normal runtime restored with TTL/CoreDMA/analyzer/MonInj/Ethernet PASS at
192.168.2.3; no fresh hardware check was performed in this review.
See [capture](../../evidence/pmu-sleep-guard-hardware-2026-10-23/README.md).

**DDR remains NOT_ADMITTED.** The seven obligations are individually assessed in
[post-guard review](../../evidence/ddr-post-guard-review-2026-10-24/README.md).
Normal guard flow excludes scheduler return, but EE remains enabled and exact
candidate exception handlers have diagnostics/error MMIO and tight terminal
loops. Continuous PC/sleep residency, ROM/reset paths, secondary-core future
release and previously accepted PS transactions remain unproven.

Next offline: linked exception-vector/helper/transitive footprint audit. Preserve
exception reporting; no broad exception masking or repeated idle snapshots as a
substitute for exclusion. No unchanged hardware capture retry is needed.


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
| PCAP | Trained-boot reads `0xA0000A46`: read_idle1/write_idle0, PL_DONE0; profile rejected and runtime restored | Reset/enable/direction interpretation and exclusive ownership unresolved; no active-transfer inference |
| Restore | Normal baseline at192.168.2.3, TTL/CoreDMA/analyzer/MonInj/Ethernet passed after latest cycle | Restoration ends the diagnostic ownership window |

## Current checkpoint (supersedes older PCAP/PL rows above)

Normal OCM model and exact BRK run physically PASS; normal runtime restored.
No-master diagnostic PL routed PS request constants and same-boot load PASS.
PCAP reset/control/direction and PL_DONE context now captured; status-only
interpretation gap narrowed, exclusive ownership remains unproven. Main remaining
work is PMU/secondary-core exclusion and historical PS transaction ownership.
Actual target preprocessing confirms disabling PM alone leaves other facilities;
FSBL may depend on PM configuration. Do not deploy reduced PMU blindly. Next
review explicit post-handoff quiescence acknowledgment while preserving boot,
rather than repeating momentary captures. See pmu-profiles-review-2026-10-23.

## Three original gaps to resolve

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


### PCAP context review — 2026-10-23

AMD initialization releases PCAP reset before transfers; FSBL later asserts it
after configuration. WR_IDLE/RD_IDLE polling belongs to transfer-specific paths.
The earlier status-only capture lacks reset/mode/direction context and remains a
failed conservative criterion, not an active-transfer proof. A four-register
read-only context plan is prepared; it is NOT_RUN and does not admit DDR writes.


2026-10-23: PCAP context eight-read capture integrated/tested offline. Physical
attempt blocked by absent exact Genesys USB UART, before reset/JTAG in both
candidate and restoration loaders. No board change; baseline not reverified.
See evidence/boot-pcap-context-unavailable-2026-10-23/assessment.json and fresh
boot-pcap-context-integration-2026-10-23 inputs. Reconnect exact board USB before
continuation. DDR admission remains closed; no completion inferred from reset.


2026-10-23 physical PCAP context PASS: two identical status0xa0000a46,
reset1/control1/direction0 observations. Reset control asserted is context,
not completion/exclusive ownership proof. Normal runtime192.168.2.3 restored
TTL/CoreDMA/analyzer/MonInj/EthernetPASS. USB blockage superseded. Full DDR
NOT_RUN/NOT_ADMITTED; PMU and PLHP0/reset epoch remain unresolved. Evidence
boot-pcap-context-hardware-2026-10-23; no repeat unchanged capture needed.
