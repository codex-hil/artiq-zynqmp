# Genesys ZU-5EV — status portu ARTIQ

Stan: 2026-10-06. **Definition of Done nie została osiągnięta.** Powstał
kompilowalny firmware diagnostyczny A53, symulowany local RTIO i wykonywany
pod QEMU kernel NAC3 na A53/AArch32, ale nie ma
jeszcze działającego runtime ARTIQ ani pomiarów hardware. Nowy bitstream
migacza Piotra zbudowano; local RTIO również zbudowano (125 MHz, timing/bitgen PASS).

Punktem bazowym jest praca Piotra: `main@e15b8a2` i `wip@b25e75b`.
Rozwój odbywa się na `bringup/genesys` wyprowadzonym z `wip`. Oryginalne
commity i pełne historie pozostają dostępne w mirrorach i bundle.

Klasyfikacja dotyczy integracji na Genesys, nie jakości bibliotek zewnętrznych:
DONE = wykonana i sprawdzona deklarowana część, PARTIAL = część implementacji,
STUB = imitacja interfejsu bez funkcji, BROKEN = wykazany błąd,
MISSING = brak integracji, OBSOLETE = rozwiązanie historyczne wymagające wymiany.
PASS w symulacji lub buildzie nigdy nie oznacza PASS hardware.

| Subsystem | Piotr | Duke | upstream / inne | Obecny status Genesys | Test / dowód |
|---|---|---|---|---|---|
| build | PARTIAL: Rust, Vivado, Vitis, Yocto | Nix/nightly 2023; własny target JSON | Cargo stable, Migen/Vivado, AMD CMake/SDT | PARTIAL: R5/A53, oba bitstreamy, PMU/FSBL i dwurdzeniowy runtime load/run/RPC PASS; pełny runtime PARTIAL | `make test hdl`; logi w evidence |
| PS | Własne TCL, eksport pinów/XCI | ZCU111 HAL i SLCR | AMD PS IP; LiteX ZynqMP | PARTIAL: zachowano TCL Piotra; wariant HPM0/125 MHz | Vivado 2025.2 blinker/local RTIO PASS; JTAG/PS/CSR hardware PASS |
| AArch64 | main: biblioteka C ABI; startup delegowany BSP | Własny startup, wyjątki, multicore | AdaCore 0.2.0, aarch64-cpu | PARTIAL: fizyczny A53/EL1 OCM PASS; DDR startup/MMU diagnostyki PASS | JTAG + UART evidence; autonomiczny boot NOT_RUN |
| R5/OpenAMP | wip: BSP C i przykład echo; Rust pusty loop | Brak równoważnej ścieżki | AMD/OpenAMP/libmetal | PARTIAL: oryginalna biblioteka kompiluje; brak wykonania kernelów | Cargo R5; OpenAMP hardware NOT_RUN |
| DDR | Dynamiczne SPD/FSBL, lokalne xfsbl_ddr_init.c | Własny SPD/PHY dla ZCU111 | AMD FSBL + Digilent BSP | PARTIAL: FSBL Piotra + AMD 2025.2 uruchomiony; DDR test 128 KiB PASS | evidence/a53-ddr-hardware-2026-10-07.json; pełny zakres/stress NOT_RUN |
| UART | MIO18–19 / 115200, BSP C | UART + generator baud | AdaCore UART/embedded-io | DONE UART diagnostic: TX i PING/PONG fizycznie PASS | `evidence/a53-ocm-hardware-2026-10-07.json` |
| GIC | R5 helper używa XScuGic/IPI | Własny GIC400 | arm-gic 0.6.1 | DONE diagnostic PPI30: fizycznie PASS, poprawiony widok EL1 NS | `evidence/a53-ocm-hardware-2026-10-07.json` |
| timer | PS TTC0 skonfigurowany; brak testu ARTIQ | Global timer/time/async delay | Generic A53 timer | PARTIAL: polling i PPI30 fizycznie PASS | Częstotliwość fizyczna niezmierzona; evidence OCM |
| clocks | TCL i FSBL PS PLL; LED counter | Własna inicjalizacja SLCR PLL | AMD; LiteX config/preset | PARTIAL: local-rtio żąda PL0 125 MHz | Estymacja counter/monotonic około 125 MHz PASS (5% tolerancji); nie precyzyjna kalibracja |
| Ethernet | ENET0 MIO26–37, MDIO76–77; Linux | GEM/PHY/smoltcp; uwagi o ograniczeniach TX | AMD GEM, Linux macb; Zynq7000 NAR3 | PARTIAL: GEM0 bare-metal DHCP/ping/TCP echo fizycznie PASS; Rust management i kernel load/run/scalar RPC fizycznie PASS | MDIO/link/DHCP/20 ping/1,129,210 B TCP PASS; rzeczywisty scalar RPC PASS |
| AXI | Historyczny read-only slave 0x80000000; usunięty z późniejszego kodu | AFI HP/HPC rejestry, bez ARTIQ | LiteX AXI2Wishbone; MiSoC CSR | PARTIAL: HPM0_FPD -> CSR 0xA0000000; naprawiony importer PS | Symulacja AXI/ID/backpressure/CSR PASS; fizyczny CSR readback przez PS DAP PASS; A53 MMIO counter via TCP PASS |
| RTIO | MISSING: tylko migacz LED | MISSING integracja ARTIQ | ARTIQ TSC/Core/SED/KernelInitiator | PARTIAL: prawdziwy upstream RTIO, 2 kanały, coarse 8 ns przy 125 MHz | Kernel→CSR timeline/input/sample i TTL ELF load hardware PASS; fizyczny loopback NOT_RUN |
| TTL output | MISSING | MISSING | ttl_simple.Output | PARTIAL: JB1/AE13, LVCMOS33 z XDC Piotra | Odstęp zboczy 50 taktów w symulacji; fizyczny determinism NOT_RUN |
| TTL input | MISSING | MISSING | ttl_simple.Input | PARTIAL: JB2/AG14, synchronizacja i timestamp FIFO | Symulowany loopback PASS; fizyczny loopback NOT_RUN |
| DMA | MISSING | PS/SD/GEM DMA ≠ RTIO DMA | ARTIQ RTIO DMA; zynq DMA adapter | MISSING: brak transportu DDR->CRI ZynqMP | NOT_RUN; suite nie zgłasza sukcesu DMA |
| analyzer | STUB serwera TCP1382 | Brak integracji | ARTIQ analyzer + NAR3 protokół | MISSING sprzętowy recorder/DDR i obsługa sieci | NOT_RUN |
| moninj | STUB serwera TCP1383 | Brak integracji | ARTIQ MonInj | PARTIAL: CSR probes/injection; TCP nadal STUB | Fizyczny CSR output probe PASS; pełny protocol NOT_RUN |
| management | STUB: handler `pass`, TCP1380 | Nie zastępuje NAR3 mgmt | artiq-zynq management | PARTIAL: Rust A53 + AMD/lwIP TCP1380; GetLog/ClearLog/read-only metadata | Aktualny artiq_coremgmt log/config oraz 9 testów hardware PASS |
| RPC/kernel | STUB: LoadCompleted/KernelFinished bez wykonania ELF | Board runtime, nie runtime ARTIQ | NAR3 loader/ksupport/RPC/unwind | PARTIAL runtime: TCP1381 → rzeczywisty loader i wykonanie CPU1 → scalar RPC PASS; TTL exports i exceptions/unwind pending | artiq_run 5/5; błędne/oversized/unsupported ELF odrzucone; ABI QEMU/hardware PASS |
| DRTIO | MISSING | Brak ARTIQ GT layer | ARTIQ protokół + GT-specyficzne PHY | MISSING; odłożone po local RTIO | Brak recovered clock/latency/link-training tests |
| SD/QSPI | PS config, boot recipes | SDIO/ADMA/FAT, ograniczenia 1.8 V | AMD SD/QSPI, Linux | PARTIAL: kod/konfiguracja bez odtworzonego boot.bin | NOT_RUN |

## Wyniki wykonane

- Pełne mirrory źródeł i pinowane submodules, w tym współczesne i historyczne
  wersje ARTIQ/Migen/MiSoC. Dokładne refs: `evidence/sources.json`.
- Historia Piotra: 58 osiągalnych commitów, dwie gałęzie, brak tagów.
  Zapisano cały log, statystyki, patch historyczny i wszystkie historyczne gitlinki.
- Naprawa wejść importera: cztery testy FAIL na `origin/wip`, pięć PASS po zmianie.
- Biblioteka main AArch64 oraz wip R5 kompilują na współczesnym stable.
  Odtworzenie przypiętych Rust 1.75/1.87 jest rejestrowane w logach buildu.
- `make test`: 12 testów host/symulacja, R5 staticlib, A53 ELF i walidator ELF.
  `make hdl`: rzeczywisty RTIO/AXI subsystem Verilog, CSR map oraz ROM init.
- Ten sam test RTIO działa z pinowanym ARTIQ Piotra oraz współczesnym ARTIQ
  `canonical/master`. To weryfikacja gateware, a nie zgodności firmware ABI.
- Nix metadata po rozwinięciu zagnieżdżonego `gen-machine-conf` przechodzi.
  Nie wykonano pełnego `nix develop` ani budowania całej closure.
- `make test-hw` bez wskazanego urządzenia zapisuje NOT_RUN i zwraca błąd.
  Nie używa symulacji jako zastępczego sukcesu hardware.

## Nowy wynik: kernel A53/AArch32 bez Vivado

`make test-kernel-abi` ma odtwarzalny runner i lokalny toolchain `.deb`
z przypiętymi wersjami/SHA-256. Wykonano test prawdziwego NAC3 kernela
na Cortex-A53 w QEMU: EL3/AArch64 → EL1/AArch32, loader M-Labs, i64,
hard-float, timeline i pusty automatyczny writeback. Przeszedł również
wariant aktualnego ARTIQ `EnvExperiment` + `TTLOut.pulse_mu()`. Celowo
błędny argument kończy test kodem 3; nie może zgłosić PASS.

Nie jest to fizyczny TTL: wywołania output są rejestrowane w modelu.
Brak obsługi aplikacyjnego RPC i unwind; cache/MMU w bare-metal probe
są wyłączone i test ten nie obejmuje ZynqMP peripherals. Przypięty
NAC3 pochodzi z 2026-05-12 i używa LLVM 19; HEAD z LLVM 23 nie był
budowany. Źródła obecnego ARTIQ pozostają bez zmian. Szczegóły:
[prototypes/kernel-abi/README.md](prototypes/kernel-abi/README.md).

## Co blokuje Definition of Done

Nie ustalono dostępnego Vivado ani dostępu do Genesys ZU-5EV. Nie użyto
niezidentyfikowanych lokalnych portów szeregowych ani urządzeń JTAG.
`make 0_platform` rzeczywiście dochodzi do uruchomienia Vivado i kończy się
`No such file or directory`. Bez niego nie uzyskano XSA/bitstreamu tego targetu.

Niezależnie od sprzętu pozostaje zasadnicza praca programowa: loader i wykonanie
kernelów, ABI kompilatora dla A53/R5, ksupport/unwind, networking i management.
Nie wolno opisywać tego jako wyłącznie problemu dostępności płytki.
Ani biblioteka Rust Piotra, ani port Duke nie są już gotowym ARTIQ core device.

## Kolejność dalszych etapów

1. Vivado: odtworzyć `blinker` PS/XSA/bitstream, sprawdzić eksport pinów i timing.
2. FSBL Piotra/AMD: UART, SPD/DDR, PMU/handoff, uruchomić diagnostykę tylko na A53#0.
3. Uruchomić i powtórzyć testy UART/DDR/timer/IRQ, zachowując raw logs.
4. Zsyntezować `local-rtio` w osobnym katalogu. Sprawdzić HPM0, zegar125 MHz,
   reset, CSR map i TTL loopback na JB1/JB2. Zmierzyć fizyczną latencję na oscyloskopie.
5. Wybrać i zamrozić kernel ISA/ABI; integrować właściwy runtime NAR3 wraz z
   management, ELF loading, ksupport i RPC. Patrz `docs/ARCHITECTURE.md`.
6. Test `artiq_coremgmt` i normalny eksperyment TTL. Dopiero potem DMA,
   analyzer i moninj TCP. DRTIO i AFCZ pozostają następne.

Każdy etap ma osobny commit i osobny rodzaj dowodu: build, symulacja albo hardware.

## Vivado i pierwsza próba JTAG — 2026-10-06

Wspólne Vivado 2025.2 zainstalowane offline; synteza kontrolna ZU-5EV PASS.
Pierwszy rzeczywisty build platformy ujawnił błąd zakresu zmiennej TCL
`artiq_variant` (plik properties jest source wewnątrz procedury); poprawiono
odwołanie na jawne globalne. Kontener wymaga `lsb-release`: bez niego
Vivado generuje wielowierszowy nagłówek hosta i niepoprawny Verilog.
Po obu poprawkach build blinker ponowiony w
`/srv/codex-hil-data/artiq-zynqmp/build-vivado/genesys-blinker`.

Połączenie hw_server/JTAG działa, lecz wykryta płytka ma `xc7a50t`,
nie Genesys ZU-5EV. Niczego nie zaprogramowano. Dowód:
`evidence/jtag-probe-2026-10-06.json`. Testy fizycznego Genesys pozostają
NOT_RUN; oczekiwanie na USB-JTAG właściwej płytki.

### Pierwszy odtworzony board bitstream — PASS

Migacz Piotra z prawdziwym PS IP/XSA zbudowano Vivado 2025.2.
Routing i bitgen PASS, WNS +2.426 ns, WHS +0.055 ns; zadane ograniczenia
czasowe spełnione. Dowody/hashe: `evidence/vivado-blinker-2026-10-06.json`.
Naprawa środowiska: `lsb-release` oraz wcześniejsze ładowanie Ubuntu
`libudev.so.1`, zgodnie z obejściem Dockera w vendorowym `bin/loader`
(który sprawdza tylko ścieżkę RHEL /lib64). Bez preloading routing kończył
się poprawnie, lecz WebTalk powodował crash realloc/libudev. Historyczne
`config_webtalk` nie istnieje w zainstalowanym 2025.2, więc nie zastosowano go.
To PASS buildu, nie hardware. Wariant local-rtio uruchomiony osobno.

### Local RTIO board bitstream — PASS

Wariant local-rtio (HPM0_FPD/CSR, dwa kanały TTL, PL0 125 MHz) przeszedł
pełny build Vivado 2025.2: XSA, synteza, routing, DRC, bitgen, csr-map.json.
WNS +2.893 ns, WHS +0.014 ns, zadane ograniczenia spełnione. DRC: zero
błędów, jedno ostrzeżenie RTSTAT-10 (net synchronizatora bez routable loads).
Zachowano raporty i ostrzeżenia vendor PS IP; PASS buildu nie zalicza
CDC/TTL/AXI hardware. Hashe: `evidence/vivado-local-rtio-2026-10-06.json`.
Fizyczne uruchomienie i runtime ARTIQ pozostają niewykonane.

## Pierwszy kontakt z fizycznym Genesys — 2026-10-07

Digilent 210383B7F02DA: JTAG wykrywa xczu5_0 i ARM DAP; debugger widzi
cztery A53. Migacz zaprogramowany do ulotnego PL przez JTAG, startup HIGH.
Odczyt PS przez XSDB PASS (PL0_REF_CTRL i UART0_REF_CTRL = 0x01010F00).
Dodatkowe raportowanie właściwości urządzenia przez Vivado zawiodło po
udanym programowaniu; zachowano surowy log i nie utożsamiamy końcowego
kodu tej sesji z sukcesem całego skryptu. Obserwacja LED oczekuje na użytkownika.
Pasywny UART 115200 na kanałach 2/3: zero danych w 5 s; funkcjonalny test
UART, boot firmware, DDR, AXI i local RTIO hardware nadal NOT_RUN.
Dowód: `evidence/genesys-hardware-2026-10-07.json`. Uprawnienia USB
nadane ręcznie przez użytkownika są tymczasowe (mogą zniknąć po reconnect).

## A53 / UART / timer / GIC — fizyczne PASS 2026-10-07

Użytkownik potwierdził miganie LED. Diagnostyka OCM na A53#0 uruchomiona
przez XSDB: UART TX PASS, PING/PONG/RX PASS, CNTPCT monotonic PASS,
przerwanie fizycznego timera PPI30 PASS (count=1 id=30 other=0). Powtórzono
po poprawkach przez zapisany runner i capture; wynik JSON i log UART:
`evidence/a53-ocm-hardware-2026-10-07.json`. Właściwy UART PS: FTDI kanał B
(by-id kończy się if01-port0), nie C/D. DDR = NOT_RUN.

Startup OCM adaptuje przypięte AdaCore start.S, pomijając DDR-zależne MMU;
oryginalny DDR build nadal się kompiluje. Naprawiono widok non-secure GICv2:
arm-gic 0.6.1 setup/ack korzystają z bitu/aliasów secure; EL1 NS potrzebuje
GICD_CTLR bit0 i zwykłych IAR/EOIR. Wyczyszczono pending SGI z boot/debug
i odróżniono je od PPI30. RX polling ma limit czasu, nie blokujące read(4).
CNTFRQ 99999000 jest stałą startupu AdaCore, nie pomiarem fizycznej
częstotliwości zegara — dokładność/częstotliwość pozostaje do walidacji.
Autonomiczny boot SD/QSPI i inicjalizacja DDR przez FSBL nadal NOT_RUN.

## PMU + FSBL + DDR + PS/PL + RTIO — 2026-10-07

Odtworzono FSBL i PMU firmware AMD 2025.2 przez SDT/empyro/CMake,
bez Vitis IDE i PetaLinux. Zachowano i skompilowano oryginalne
`xfsbl_ddr_init.c` Piotra (dynamiczne SPD), zamiast zastępować DDR
statycznymi parametrami. GNU Arm 13.2.Rel1 pobrany z oficjalnego repo Arm,
SHA archiwum zapisany w evidence; PMU używa dostarczonego GCC MicroBlaze.

Pierwsza próba FSBL bez PMU: DDR inicjalizował się, lecz handoff kończył
się ERROR_PM_INIT 0x6050. Naprawa: PMU przed FSBL, zgodnie z
[AMD UG1137](https://docs.amd.com/r/2021.2-English/ug1137-zynq-ultrascale-mpsoc-swdev/Loading-PMU-Firmware-in-JTAG-Boot-Mode).
Pełna ścieżka PASS (Exit from FSBL), DDRC STAT=1. Powtórzony A53 DDR
startup i test 128 KiB czterema wzorcami z cache maintenance PASS;
UART PING/PONG i PPI30 nadal PASS. Autonomiczny boot oraz długi stress
całej pamięci nadal NOT_RUN.

Local-rtio bitstream zaprogramowany do PL, PL0 divisor ustawiony z jego
TCL (125 MHz nominalnie), AFI i reset/isolation z wygenerowanego PS IP.
PS DAP zapis/odczyt CSR 0xA0000000 PASS, RTIO counter monotonic PASS,
zaplanowany impuls sprawdzony wewnętrzną sondą TTL PHY high/low PASS,
async errors=0. To nie potwierdza fizycznego TTL ani deterministycznej
latencji na pinie; użytkownik odłożył zworkę JB1→JB2.
GEM0 MDIO: PHY15 ID 2000A231, BMSR796D: link=1, autoneg_done=1.
Pakiety Ethernet i produkcyjny ARTIQ runtime nadal NOT_RUN/MISSING.
Dowód: `evidence/genesys-fsbl-rtio-hardware-2026-10-07.json`.

XSDB odrzucał PL CSR spoza swojej mapy: `force-mem-accesses 1`
użyte tylko w runnerze wyraźnie przeznaczonym dla local-rtio. Stary cache
`.Xil` powodował błąd XML open_hw_manager; izolowany katalog pracy pomógł.

`make test-hw-jtag` dodane: host uruchamia UART capture, diagnostykę A53
DDR/timer/IRQ, probe PS↔PL/RTIO oraz GEM0 MDIO. Seria powtórzona fizycznie:
10 diagnostyk PASS, Ethernet packets / physical TTL / DMA NOT_RUN.
Runner świadomie zwraca kod 2 (suite niekompletna), nigdy pełny PASS.
Dowód: `evidence/jtag-hardware-suite-2026-10-07.json`.

## Ethernet GEM0 — fizyczne pakiety PASS 2026-10-07

Odzyskany PS/FSBL Piotra wykorzystano do startu gotowego przykładu AMD
`lwip_echo_server` (2025.2, emacps 3.23, lwIP 2.2.0, xiltimer 2.3),
zbudowanego przez SDT/empyro/CMake i GNU Arm 13.2.Rel1. Nie przepisano
sterownika GEM ani obsługi jego DMA do Rusta. Vendor checkout/instalacja
pozostały bez zmian; patche dotyczą wygenerowanych kopii.

Poprawki: własny lokalnie administrowany MAC dla tej płyty, poprawna informacja
o porcie 7, jawne błędy DHCP bez niezweryfikowanego statycznego fallbacku,
20 s zamiast 5 s timeoutu TI RGMII autonegotiation. Adres PHY15 był
poprawnie wykrywany; timeout upływał przed odczytem kończącym piątą iterację.

Warm JTAG/processor-only reset zachowywał stan GIC z poprzedniego EL1 NS
programu. Zarejestrowano TTC0 pending/active, RPR=0xA0, brak tyknięć DHCP;
zakończenie znanego outstanding IRQ wznowiło licznik. Docelowy runner
wykonuje PS system reset, następnie PMU/FSBL i dopiero AMD EL3 aplikację.
Końcowy firmware nie zawiera ręcznej poprawki GIC. Przejście z diagnostyki
Rust EL1 do C EL3 wymaga tej ścieżki; reset procesora nie jest cold resetem PS.

Końcowy firmware odtworzony od zera, następnie pełny automatyczny runner
uruchomiony fizycznie: PHY15 1 Gb/s, DHCP 192.168.2.16, MAC
02:38:3b:7f:02:0d, 20/20 ICMP (0% loss), 1080 byte-exact TCP echo
przez 5 połączeń, 1,129,210 bajtów. GEM liczniki: TX1174, RX1238,
TX underrun/RX FCS/alignment/resource=0. Hashe ELF i użytych źródeł oraz
logi są w `evidence/ethernet-build-2026-10-07.json` i
`evidence/ethernet-hardware-2026-10-07.json`. DHCP adres może się zmienić.

Polecenia `make test-hw-ethernet` i `make test-hw-ethernet-bringup` dodane;
drugie obejmuje identyfikację JTAG, reset/start, UART/DHCP, MAC, ICMP, TCP
i MAC counters. Instrukcja: `diagnostics/ethernet/README.md`.
PASS dotyczy początkowego ruchu pakietowego, nie długiego stressu, link flap
lub prędkości 10/100 Mb/s. GEM DMA działa w tym teście; RTIO DMA to osobny
subsystem nadal MISSING. Networking/RPC/management produkcyjnego ARTIQ
nadal MISSING; ten ELF uruchamia diagnostykę echo, nie ARTIQ core device.

## Rust A53 + Ethernet + management — integracja fizyczna 2026-10-07

Zachowano architekturę Piotra C BSP → Rust staticlib. Nowy mały no_std
`boards/genesys_zu-5ev/2_firmware_a53` obsługuje aktualny protokół management
ARTIQ; AMD GEM/lwIP pozostaje sterownikiem i transportem. Nie przepisano
GEM do Rust ani nie przenoszono projektu do LiteX. Sześć testów protokołu
host PASS; świeży build host Rust + kontener AMD SDT/CMake PASS.
Reproducer: `scripts/build_a53_services.sh`; instrukcje i ograniczenia:
`diagnostics/services/README.md`.

Fizycznie PASS: aktualny CommMgmt, prawdziwy CLI artiq_coremgmt log i config,
ClearLog, fragmentacja/coalescing, równoległe sesje, odrzucenie zbyt długiego
klucza i nieobsługiwanego zapisu. Licznik local RTIO odczytany przez A53 MMIO
→ Rust → management TCP; zmierzona nominalna częstotliwość około 125 MHz
(tolerancja testu 5%, nie precyzyjna kalibracja). Ethernet po integracji nadal
20/20 ICMP, 1080 TCP echo / 1,129,210 bajtów, GEM błędy=0.
Dowody: `evidence/a53-services-hardware-2026-10-07.json`,
`evidence/a53-services-network-2026-10-07.json`,
`evidence/a53-services-build-2026-10-07.json`.

Naprawiona sekwencja startu debug: PS system reset → PMU/FSBL → programowanie
PL local-rtio → wygenerowany PS/PL setup i DAP CSR preflight → aplikacja A53.
Programowanie PL przed resetem PS nie zapewniało działającej konfiguracji:
A53 i DAP blokowały się na AXI. Zachowano nieudany test jako
`evidence/a53-services-missing-pl-2026-10-07.json`. Runner teraz sprawdza
rzeczywisty dostęp do CSR przed uruchomieniem CPU. To JTAG debug boot,
nie jeszcze samodzielny SD/QSPI BOOT.BIN.

Status runtime nadal **management-only**, nie pełny ARTIQ core device.
Port kernel1381 nie działa; loader/wykonanie kerneli, RPC, analyzer, moninj,
RTIO DMA i eksperyment fizyczny pozostają MISSING/NOT_RUN. Unsupported write,
flash, reboot i streaming PullLog zwracają błąd; brak fikcyjnego sukcesu.
Physical TTL input/output wymaga osobnego testu; zworka JB1-JB2 odłożona.

## Kernel ABI i loader na fizycznym A53 CPU1 — 2026-10-07

Nie zaczęto nowego loadera: wykorzystano zachowany upstream M-Labs ARM ELF
loader oraz działający NAC3/Cortex-A9 prototyp. CPU0 pozostaje AArch64
management/Ethernet, CPU1 wykonuje diagnostykę w EL1/AArch32 po stubie EL3.
Prawdziwy kernel aktualnego ARTIQ Core/EnvExperiment/TTLOut wykonany na
fizycznym CPU1: i64/hard-float/NEON/timeline/empty writeback PASS. Wywołania
RTIO output celowo trafiają do modelu; fizyczny eksperyment NOT_RUN.
Osobny realny odczyt PL RTIO counter z CPU1 AArch32 PASS. Umyślnie błędny
argument i64 został odrzucony, bez hardware exception; kontrola negatywna
PASS. CPU0 management przed i po obu wariantach PASS.

Rzeczywisty sprzęt ujawnił alignment fault: include_bytes! dawało ELF o
wyrównaniu 1, upstream loader wykonywał word load. Dodano aligned wrapper
własnego prototypu; nie modyfikowano formatu kernela ani kodu loadera.
Wysokie wektory resetowe SCTLR.V wyłączono w diagnostycznym stubie; fault
LR/SPSR zapisuje mailbox. XSDB cache-sync nie obsłużył przełączenia privilege
AArch32; dedykowany uncached mailbox odczytywany przez DAP AP0. To nie
polityka produkcyjnego cache/MMU. Pełna regresja QEMU pozytywna/negatywna/
aktualny ARTIQ również PASS po zmianie wyrównania.

Reproducer i mapa zarezerwowanej pamięci:
`diagnostics/kernel-a53/README.md`; `make test-hw-kernel-cpu1`.
Dowody: `evidence/kernel-cpu1-hardware-2026-10-07.json` oraz
`evidence/kernel-abi-regression-2026-10-07.json`.
Loader jako biblioteka i ABI mają fizyczny proof; sieciowe upload/load/run,
inter-core channel, allocator/cache produkcyjne, prawdziwe RTIO exports,
aplikacyjny RPC i exception/unwind nadal nie są zintegrowane. TCP1381 nadal
nie jest wystawiony jako działający runtime. Eksperymenty TTL odłożone
zgodnie z prośbą użytkownika do jutra.

## Host ARTIQ CLI — 2026-10-07

Osobny venv `venvs/artiq-host` na dysku danych, wspólne launchery
artiq_run/artiq_compile/artiq_coremgmt/artiq-host w ~/.local/bin.
Aktualny przypięty ARTIQ + kompatybilny sipyco + wcześniej przetestowany
NAC3/LLVM19, bez zmiany oryginalnych reference checkoutów. CLI help,
pip check, import NAC3, offline kompilacja GenesysTTL (ARM32 ELF 2620 B)
i rzeczywisty odczyt management log z płyty PASS. duration pulse_mu wymaga
jawnego numpy.int64, poprawiono przykład. Fizycznego eksperymentu nie
uruchamiano; firmware nadal management-only. Instrukcja: docs/ARTIQ_HOST.md;
dowód: evidence/artiq-host-install-2026-10-07.json.

## Sieciowy kernel runtime i rzeczywisty RPC — 2026-10-07

Połączono dotychczasowe etapy: C AMD/lwIP + Rust management na CPU0/AArch64
oraz Rust worker na CPU1/EL1 AArch32. Użyto zachowanego upstream ELF loadera;
serializer RPC i libio są niemodyfikowanymi kopiami M-Labs z przypiętego
commita. Nowa warstwa ZynqMP obejmuje startup, kanał shared DDR/cache,
transport TCP i wiązania API, nie nowy loader/protokół/driver GEM.
Alokacja przez istniejący linked_list_allocator 0.10.5: runtime i kernel
mają osobne sterty po 512 KiB. Pierwszy prawdziwy upload ujawnił brak eksportu
malloc; dodano malloc/free i realny alokator zamiast potwierdzać nieudany load.

Prawdziwy upstream artiq_run wykonał pięć świeżo kompilowanych kerneli
bez wyjść TTL. Token i64, rzeczywisty counter RTIO i float dotarły przez RPC
do hosta; float 3.75 wrócił na CPU1 i został potwierdzony drugim RPC.
Automatic empty asynchronous writeback obsługiwany upstream codecem.
LoadCompleted jest wysyłany po udanym dyld::load/relokacjach i sprawdzeniu
__modinit__; KernelFinished po rzeczywistym powrocie entry point.
Runtime mode: kernel-bringup. To nadal częściowy, nie produkcyjnie kompletny
ARTIQ core device.

Fizyczne PASS: błędny/out-of-bounds ELF, oversized upload (1 MiB limit),
nieobsługiwany TTL ELF (LoadFailed: unresolved rtio_output), fragmentowany
upload, jeden właściciel kernela, metadata management równolegle z RPC,
shared-counter-latch guard, repeated artiq_run oraz wszystkie dziewięć
management testów. GEM nadal 20/20 ICMP, 1080 TCP echo / 1,129,210 B,
liczniki błędów zero. Guard odrzuca CPU0 management odczyt counter podczas
pracy CPU1; hardware latch jest wspólny i nie powinien mieć dwóch czytelników.

Boot: reset PS → PMU/FSBL → PL/preflight → CPU1 worker → CPU0 networking.
Nowy runner CPU0 zachowuje pracę CPU1; stary halting-all-cores runner
pozostaje tylko diagnostyczny. Cache-maintenance CPU0 pochodzi z AMD;
CPU1 MMU/cache wyłączone zgodnie z wcześniej sprawdzonym proofem. Docelowa
polityka MMU/izolacji i cancellation/watchdog nadal PARTIAL. Initial timeout
postępu 30 s; RPC event max4096 B; scalar returns tylko n/b/i/I/u/U/f.
Wyjątki/unwind/host RPCException i complex returns wymagają dalszej integracji;
fail-stop wymaga restartu workera i nie raportuje fałszywego KernelFinished.

Instrukcja: boards/genesys_zu-5ev/3_kernel/README.md.
Test: make test-hw-network-kernel lub scripts/test_network_kernel_hw.py.
Dowody: evidence/network-kernel-{build,hardware,management,ethernet}-2026-10-07.json.
TTL exports jeszcze nie włączone; fizycznych impulsów/loopback nie uruchamiano.
RTIO DMA/analyzer/moninj/DRTIO nadal pending. Następny etap: rzeczywiste
rtio_output i TTL input, zgodnie z prośbą użytkownika eksperymenty jutro.

## Kernel → rzeczywisty local RTIO — 2026-10-07

Eksporty rtio_output, rtio_input_timestamp i rtio_input_data wiążą teraz kernel
CPU1 z istniejącym RTIO/CSR przez PS HPM0. now_mu/at_mu/delay_mu używają
64-bitowego rtio_now w PL, zamiast software NOW. Kolejność zapisów oparta na
M-Labs rtio_csr.rs: target, dane LSW (commit), status; 64-bit MSW→LSW.
Adresy oraz liczby słów generowane z mapy faktycznego bitstreamu. Własna
warstwa nie zastępuje RTIO/SED ani protokołu ARTIQ. Async errors przy Finished
pochodzą z rzeczywistego CSR i są write-one-to-clear, zamiast stałej zero.

Hardware PASS: wartość timeline 0x1234567887654321 i delay125, pusty input
FIFO zwraca -1, zaplanowany sample wejścia channel1/address3, timestamp
+10 taktów i odczyt danych 0/1, TTL ELF relocation bez uruchomienia. Zapis
sample jest rzeczywistym zdarzeniem RTIO, ale nie przełącza pinu wyjściowego
JB1. Pięć ponownych kerneli/RPC i management guard PASS. Kontrola negatywna
sample w przeszłości: PL o_status=2, mailbox RTIOUnderflow, startup-failed
bez fałszywego Finished; CPU0 management pozostaje dostępny. Worker wymaga
restartu po błędzie, nie obsługuje jeszcze catchable exceptions/unwind.

Build/simulation nie zastępują fizycznego pomiaru TTL. Physical JB1 output,
JB1→JB2 edge loopback, pulse-width/deterministic latency nadal NOT_RUN,
zgodnie z wcześniejszym odłożeniem eksperymentów. Wide output, tuple input,
DMA/analyzer/moninj/DRTIO nadal pending. Test bez zworki:
make test-hw-rtio-kernel; dokumentacja boards/genesys_zu-5ev/3_kernel/README.md.
Poprzednie wpisy „TTL exports pending” opisują historyczne obrazy.

Final physical runtime restored after the negative control:
CPU0 build-vivado/rtio-kernel-services, CPU1 build/kernel-worker-rtio-final.
Evidence: evidence/rtio-kernel-{build,hardware,negative,ethernet,management}-2026-10-07.json.
Prepared normal ARTIQ GenesysLoopback (100 us pulse): offline compilation and
on-board relocation PASS, execution NOT_RUN until physical jumper testing.

## Physical JB1→JB2 attempt — 2026-10-08

User fitted the jumper. First actual artiq_run loopback reached CPU1 RPC
but failed with connection reset; no valid edge result, hence NOT_VALIDATED.
Recovery/inspection blocked by USB write ACL lost after host restart:
Genesys serial210383B7F02D is USB001/006, codex-hil has read-only access.
Current restarted hw_server container is 172.17.0.2 (previous .3 stale).
CPU0 management remains responsive. Both-edge/100 us width fixture compiles;
hardware execution pending diagnosis/recovery, not declared PASS.
Evidence: evidence/ttl-loopback-2026-10-08.json.

USB access restored 2026-10-08. Mailbox showed unsupported host RPCException
from the first failed validation, not PL underflow (o_status=0). Full runtime
recovery passed Ethernet tests. Updated both-edge fixture reports FAIL
without throwing RPCException; runner rejects FAIL even when artiq_run exits0.
Physical attempt still FAIL: rising/falling timestamps -1. Independent
moninj override drives output probe 0→1, but input probe stays0. Pins AE13/
AG14 verified against Digilent master XDC. Jumper placement/contact needs
inspection; do not declare TTL/loopback PASS. Output override removed and
output returned low; worker and management remain running.
`make test-hw-ttl-loopback` repeats 10 genuine artiq_run kernels and validates
both edges, exact12500mu/100us width, no extra edge and fixed sampled latency.
