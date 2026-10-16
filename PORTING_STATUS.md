# Genesys ZU-5EV — status portu ARTIQ

Stan: 2026-10-08. **Pełna Definition of Done nie została osiągnięta.**
Fizyczny Genesys wykonuje standardowe kernele ARTIQ przez Ethernet z RPC,
TTL loopback i local CoreDMA (216 impulsów/432 zbocza); szczegóły i granice
w docs/CORE_DMA.md. To runtime integracyjny, nie kompletny standardowy core.
Starszy obraz SD przeszedł cold boot; nowy obraz CoreDMA jeszcze NOT_RUN.
Aktualny priorytet: satelita DRTIO do istniejącego Kasli master dla przyszłego
DAC AD9172. PHY GTHE4 ma build i fizyczny internal-PMA PRBS7 PASS; symulacje protokołu PASS;
fizyczny link i recovered-clock/jitter-cleaner testy pozostają NOT_RUN.

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
| RTIO | MISSING: tylko migacz LED | MISSING integracja ARTIQ | ARTIQ TSC/Core/SED/KernelInitiator | PARTIAL: prawdziwy upstream RTIO, 2 kanały, coarse 8 ns przy 125 MHz | Kernel→CSR i fizyczny JB1→JB2 TTL loopback 10/10 PASS; 100 us, stałe15mu |
| TTL output | MISSING | MISSING | ttl_simple.Output | PARTIAL: JB1/AE13, LVCMOS33 z XDC Piotra | Odstęp zboczy 50 taktów w symulacji; fizyczny determinism NOT_RUN |
| TTL input | MISSING | MISSING | ttl_simple.Input | PARTIAL: JB2/AG14, synchronizacja i timestamp FIFO | Symulowany loopback PASS; fizyczny loopback NOT_RUN |
| DMA | MISSING | PS/SD/GEM DMA ≠ RTIO DMA | ARTIQ RTIO DMA; zynq DMA adapter | PARTIAL: local scalar CoreDMA API + persistent DDR + FPGA playback PASS; wide/DDMA pending | core-dma-hardware-2026-10-08.json:216 pulses/432 edges; lifecycle/errors PASS |
| analyzer | STUB serwera TCP1382 | Brak integracji | ARTIQ analyzer + NAR3 protokół | MISSING sprzętowy recorder/DDR i obsługa sieci | NOT_RUN |
| moninj | STUB serwera TCP1383 | Brak integracji | ARTIQ MonInj | PARTIAL: CSR probes/injection; TCP nadal STUB | Fizyczny CSR output probe PASS; pełny protocol NOT_RUN |
| management | STUB: handler `pass`, TCP1380 | Nie zastępuje NAR3 mgmt | artiq-zynq management | PARTIAL: Rust A53 + AMD/lwIP TCP1380; GetLog/ClearLog/read-only metadata | Aktualny artiq_coremgmt log/config oraz 9 testów hardware PASS |
| RPC/kernel | STUB: LoadCompleted/KernelFinished bez wykonania ELF | Board runtime, nie runtime ARTIQ | NAR3 loader/ksupport/RPC/unwind | PARTIAL runtime: TCP1381 → rzeczywisty loader i wykonanie CPU1 → scalar RPC, physical TTL i native exception/unwind/recovery PASS; complex returns/cancellation pending | artiq_run/RPC 5/5; TTL10/10; exception suite30 experiments PASS; ABI QEMU/hardware PASS |
| DRTIO | MISSING | Brak ARTIQ GT layer | ARTIQ protokół + GT-specyficzne PHY | PARTIAL: board GTH diagnostic + internal PMA PRBS7 hardware PASS; satellite integration MISSING | 3 reset/negative-control/recovery cycles; 19 legacy/19 current RTL tests; remote link NOT_RUN |
| SD/QSPI | PS config, boot recipes | SDIO/ADMA/FAT, ograniczenia 1.8 V | AMD SD/QSPI, Linux | PARTIAL: physical SD BOOT.BIN PASS; QSPI NOT_RUN | sd-cold-boot-2026-10-08.json |

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

## Physical TTL milestone — PASS, 2026-10-08

After user corrected the jumper from opposite rows to adjacent JB1/JB2,
10/10 standard artiq_run experiments passed on the physical board. Rising
and falling timestamps both present, width12500mu=100us in every run,
loopback latency15mu=120ns identical across10 runs, extra edge=-1. This
validates the actual kernel→local RTIO→JB1→wire→JB2→input FIFO→host RPC path.
Measured latency includes output pipeline, wire/input and synchronization;
it is not isolated pin propagation latency or external oscilloscope accuracy.
Management remains active after the series. Physical output/input and basic
experiment milestone now PASS, superseding earlier NOT_RUN/FAIL entries.
Production core completeness (exceptions, DDR qualification, standalone boot,
DMA/analyzer/moninj/DRTIO) is not claimed. Evidence ttl-loopback-2026-10-08.json;
initial failed attempt retained in ttl-loopback-initial-failure-2026-10-08.json.

## Native kernel exceptions and recovery — PASS, 2026-10-08

Integrated preserved M-Labs eh_artiq/libdwarf/libunwind and LLVM ARM EHABI
sources at the existing pinned artiq-zynq revision. No replacement unwinder,
DWARF parser or exception protocol. ZynqMP adapters provide exidx lookup,
explicit ARM invocation boundary, packet marshaling and recovery handshake.
Catchable exceptions: kernel ValueError, actual RTIOUnderflow/RTIOOverflow,
and host RPC ValueError. Reraise and finally PASS. Uncaught exceptions use
standard KernelException wire layout and reconstruct the actual Python type,
message and decoded device traceback. No false KernelFinished on error.

Final hardware suite: 3 cycles /30 artiq_run invocations, including reuse of
the identical TCP connection after a host-caught device error; each uncaught
kernel/RPC/RTIO error followed by fresh compile/load/execute/RPC without JTAG
or PS/PL reset. Counter continuous. Real input FIFO64 entries overflowed by80
scheduled samples, caught/reset successfully. Same-connection traceback check
also separately PASS with source filename/line/function from actual kernel.

On uncaught exception CPU0 copies the bounded packet before ACK. CPU1 resets
local RTIO, re-enters polling on a fresh stack and rebuilds private heaps;
old library invalidated, READY completes recovery. CPU0/network/GIC/PS/PL
keep running. Initial Vec packet used unaligned word stores and faulted under
MMU-off; bytewise volatile marshaling fixed it. Reused upstream abort handler
removed duplicate C abort; native LLVM objects replace bitcode LTO for GNU ld.
Rust/C unwind tables and linker exidx/extab bounds now explicit.

Regression: network/RPC5/5 plus native underflow/recovery PASS, physical TTL
10/10 (100us, latency15mu=120ns fixed), management9 tests PASS, GEM errors0.
Current runtime: build-vivado/eh-kernel-services + build/kernel-worker-eh-final.
Reproducer make test-hw-kernel-exceptions; evidence/kernel-exceptions-*-2026-10-08.json.
Historical pre-exception images/probes still describe fail-stop behavior.
Remaining: arbitrary hardware traps/Rust panic, cancellation/disconnect and
30s watchdog recovery, metadata>4096B, complex returns, MMU/cache/DDR production
qualification, autonomous SD/QSPI boot, DMA/analyzer/moninj/DRTIO.

## Standalone SD image — packaged, cold boot NOT_RUN (2026-10-08)

Built 3,413,000-byte BOOT.BIN with existing Piotr DDR/SPD FSBL, AMD PMU,
local-RTIO PL, current CPU0 runtime and embedded CPU1 worker. CPU1 bridge
clears cold mailbox and enters the verified EL1/AArch32 worker. CPU0 startup
waits at most five seconds for READY. Bootgen partition inspection confirms
CPU1 entry0x20000000, worker load0x20200000 and final CPU0 EL3 handoff.
Generated PS clock/AFI and AMD FSBL post-bitstream isolation/reset match
the tested JTAG sequence; actual SD boot remains NOT_RUN.

Embedded worker + updated CPU0 booted through JTAG: DHCP, ICMP20/20,
1080 TCP echo exchanges and zero GEM errors PASS. Genuine ARTIQ physical
TTL loopback10/10 PASS, 100us pulse and fixed120ns input latency.
This validates firmware changes, not BootROM/SD loading or FSBL PL loading.
Evidence: sd-boot-image-2026-10-08.json, sd-worker-jtag-2026-10-08.json,
sd-worker-ttl-2026-10-08.json. Reproducer/docs: docs/SD_BOOT.md.
No card/flash was written or formatted. Card availability/data preservation
awaits user information; no removable block device is visible on the host.

2026-10-08: user-provided32GB USB-reader card identified as /dev/sdc1
(28.8GiB FAT). Original System Volume Information/TLGLOG backed up on
large disk and preserved on card. BOOT.BIN3,413,000bytes copied, fsync/sync
and readback SHA-256 match PASS. Evidence sd-card-write-2026-10-08.json.
Cold board SD boot still NOT_RUN; card unmount requires greg sudo.

## Autonomous cold SD boot — physical PASS, 2026-10-08

User moved verified32GB card into J9, selected JP3 SD and switched board
on after UART capture armed. Log explicitly reports SD1 level-shifter boot,
BOOT.BIN, successful PL programming, all partitions loaded, CPU1 release
at0x20000000 and final CPU0 handoff. No JTAG download, register setup or
reset during this test. Both core services started, DHCP192.168.2.16.

Post-boot acceptance: management9 tests/actual artiq_coremgmt PASS; network
kernels5/5 plus native underflow/recovery PASS; physical TTL loopback10/10
(100us, fixed120ns input latency) PASS; Ethernet ICMP20/20 and1080 TCP echo
exchanges PASS; native exception suite3 cycles/30 invocations PASS, including
same-connection recovery and real device traceback. Evidence sd-cold-boot-*
including complete UART log and SHA-256 linked to written SD image.

One cold power cycle tested. Earlier SD NOT_RUN notes are historical.
DDR/cache/MMU production qualification, repeat cold boots, fatal-trap/timeout
recovery, DMA/analyzer/moninj/DRTIO and QSPI remain incomplete.

## Hardware RTIO DMA engine — PASS, 2026-10-08

Preserved M-Labs artiq-zynq AXI DMA reader connected to ZynqMP HP0(64-bit
data/49-bit address), upstream RecordSlicer/TimeOffset/CRIMaster and CRISwitch.
Existing CSR banks/addresses preserved; DMA bank3 and selector bank4 added.
DDR record buffer0x22000000 filled through DAP, autonomous PL playback.
Five hardware plays:20 pulses/40 physical JB1→JB2 edges match every expected
timestamp, width100us and fixed input latency120ns; AXI/RTIO errors zero.
Two deliberately late DMA plays correctly report native underflow with
channel1,timestamp0,address2; ACK clears error and next playback passes
without PS/PL reset. Test scripts/test_dma_jtag_hw.py / make test-hw-dma-engine.

Full bitstream timing PASS WNS+2.933ns,WHS+0.012ns at125MHz.15 RTL tests PASS.
Initial unrestricted synthesis terminated137 without RTL error; two-thread
retry completed. Reproducer scripts/build_rtio_dma.sh. Debug reset now selects
volatile alternate JTAG BEFORE system reset, preventing the inserted SD image
from racing FSBL download. New matching PS FSBL/PMU also built/booted.

Regression: DHCP/ICMP20/20/TCP echo1080/GEMerrors0 PASS, regular artiq_run
TTL10/10 PASS, native exception suite10 invocations PASS including recovery.
Evidence dma-build/engine-*/ethernet/ttl-regression/exceptions-regression.
Current board runs DMA gateware through JTAG with existing services/worker;
validated autonomous SD image remains unchanged and contains no DMA engine.

DMA overall PARTIAL: CoreDMA prepare_record/retrieve/playback_handle exports,
persistent named trace storage, lifecycle/limits and API hardware tests still
missing. No claim that ordinary ARTIQ CoreDMA experiments already work.
Next step reuse M-Labs recorder/runtime with ZynqMP storage/CSR adapters.

## Standard local CoreDMA API — physical PASS, 2026-10-08

Preserved M-Labs recorder/runtime originals and standard ABI/record format.
ZynqMP adapters redirect recording output, use32 fixed64KiB uncached DDR
slots at0x22000000–0x22200000 and drive already verified FPGA DMA CSRs.
Committed traces survive ELF replacement and uncaught exception recovery;
abandoned recorder cleared without touching other traces or resettable heaps.
NAC3 tuple ObjectHeader changed return ABI: plain older16-byte DmaTrace
initially decoded wrong pointer; pinned compiler needs24 bytes/header8.
Adapter/compile-time offsets fixed this; CoreDMA handle list also PASS.

Final suite3 cycles/21 artiq_run invocations,216 validated pulses/432 actual
JB1→JB2 edges. Named/handle playback,100us and64ns pulses with64ns gaps,
fixed120ns input latency PASS. Timeline restore/advance, overwrite, erase,
missing/stale handles, full32 slots, trace/name bounds, empty name/trace,
nested recording, DDMA rejection, invalid pointer, native DMA underflow/ACK
and next playback PASS. Uncaught host DMAError/device traceback then next
kernel PASS. Stored trace survives uncaught ValueError during another record
with same TCP connection. Regression TTL10/10, exception10, management9,
Ethernet DHCP/ICMP20/TCP1080/GEMerrors0 PASS. See evidence/core-dma-* and
docs/CORE_DMA.md; make test-hw-core-dma.

Final worker build/kernel-worker-dma-final. New BOOT.BIN prepared at
build/sd-core-dma-2026-10-08, packaging PASS; its cold SD boot NOT_RUN.
Current physical card still earlier validated non-DMA image. Current board
runs CoreDMA firmware through JTAG. Wide RTIO/DDMA, general hardware-stall
recovery and production DDR/MMU/cache qualification remain incomplete.


2026-10-08 DRTIO reprioritized for Kasli-master DAC satellite. Board clock
recovery resources confirmed in Digilent documentation: Si5342 IC46,
FPGA-driven SFP_REC_CLK input, cleaned GTH quad224 reference. Design and
validation sequence: docs/DRTIO_CLOCKING.md. No physical DRTIO/clock-lock
test has run; GTHE4 adapter/profile/reset FSM still missing. Existing
local RTIO firmware and bitstreams were not changed.


## 2026-10-08: DRTIO PHY preparation

Separate diagnostic GTHE4 X0Y7 raw20-bit PHY at2.5Gb/s synthesized with
Vivado2025.2 for both125MHz and factory156.25MHz reference profiles. Generated
RXOUTCLK and RX/TX user clocks are125MHz in both cases. PRBS/loopback/PLL
and reset status ports exposed. OOC synthesis is not board implementation
or hardware validation. Diagnostic elastic buffers remain enabled; final
deterministic adapter/satellite/reset and clock-forwarding top are missing.

Reproducer: make drtio-phy / make test-drtio-protocol; documentation in
diagnostics/drtio/README.md. Original Piotr ARTIQ1461cf9 and current
ARTIQ486e8f8 each passed19 DRTIO RTL simulations. Build verifier rejects
wrong line rate and incomplete synthesis. Evidence: drtio-phy-ref125,
drtio-phy-ref156, drtio-protocol-simulation and drtio-phy-validator-negative
2026-10-08 JSONs. Existing physical runtime was not reprogrammed.

Build compatibility: initial synth_ip in project mode produced Vivado
12-5447; replaced by create_ip_run/launch_runs/wait_on_run plus completion
check. An intermediate launch without create_ip_run failed12-821; corrected
and final two profiles synthesized successfully. Logs remain in
build/drtio-phy-2026-10-08. Vendor CPLL helper warnings are retained.

Existing Digilent HDMI Si5342 driver/profile and revC clock constraints
located in archived sources; exact origins/hashes in clock-source-origins.json.
HDMI profile is not suitable directly for125MHz SFP lock. Its I2C error
handling needs explicit propagation before reuse. Physical chip readback,
board-revision pin confirmation, profiles and lock tests still pending.


## 2026-10-08: physical GTH internal PMA loopback

Separate diagnostic board bitstream reuses Piotr PS/HPM0/Migen integration,
selects SFP (D10=1) and keeps module TX disabled (AB13=1). GTH X0Y7 uses
unchanged factory 156.25MHz reference, 2.5Gb/s raw20 PHY, RX/TX word clocks
125MHz. Three reset cycles passed CPLL/reset/clock status, clock ratios
within 1%, zero settled PRBS7 errors. TX PRBS15 / RX PRBS7 negative control
registered >12 million error cycles on each trial; after full GTH reset,
PRBS7 recovered with zero errors. Switching patterns alone did NOT recover
in the initial trial; the diagnostic does not expose RXPRBSCNTRESET, so
explicit reset is required. These are error-cycle counts, not BER estimates.

Full board build passed DRC and corrected timing: WNS +2.783ns, WHS +0.017ns,
all three Gray bus-skew checks passed (>6ns slack against 8ns requirement).
Build used resumed synthesis/routing after checked constraints corrections;
all initial and resumed logs are retained in build-vivado/
drtio-diagnostic-relocated-2026-10-08. This is not a clean-build claim.
Compatibility fixes are local to diagnostic platform/build scripts:
separate each IP's output directory, relocate only copied JSON XCI generation
paths, replace obsolete project-mode synth_ip with IP runs, select flip-flops
rather than similarly named logic when applying Gray constraints, and target
first-stage mr_ff register D pins (old Migen targets nets, ineffective here).
Original IP sources and archived Migen remain unchanged.

Evidence: evidence/drtio-top-build-2026-10-08.json and
evidence/drtio-phy-loopback-2026-10-08.{json,log}. Remote Kasli link, optical
path, RX symbol alignment, deterministic latency, Si5342 recovered-input
lock and ARTIQ satellite firmware remain NOT_RUN/MISSING. Internal PMA
loopback does not validate the external SFP/mux electrical path. No Si5342
configuration writes were performed.


After diagnostic testing, the prior CoreDMA PS/PL/firmware was restored.
DHCP, 20/20 ICMP, five connections/1080 byte-exact TCP echo exchanges and
zero GEM error counters passed. Standard artiq_run genesys_dma.py then
passed handle/name playback with 8 physical pulses/16 exact loopback edges.
Evidence: evidence/drtio-restored-core-2026-10-08.json. The board is left
running the integration runtime at192.168.2.16, not the GTH diagnostic.

## 2026-10-08: Kasli v2.1 master build in preparation

User requested standard Kasli at its latest hardware revision: v2.1,
Artix-7 XC7A100T, not Kasli-SoC. Separate upstream worktree builds a test
master at125MHz/2.5Gb/s, no EEMs and WRPLL disabled. Same ARTIQ486e8f8
snapshot as current Genesys host/protocol work; hardware revision selection
does not imply compatibility with a different existing system JSON.
Bootloader, ksupport and master runtime compile/link PASS with upstream
Rustnightly2021-09-01 and LLVM/Clang/LLD20.1.8. ELF32 RISC-V and runtime.fbi
length/CRC32 validation PASS. No successful Kasli bitstream or physical
Kasli test yet. Shared Vivado initially has only ZynqMP device support;
XC7A100T is missing. Installed-tree Add action requires renewed AMD token.
117 relevant offline packages (~2.47GB with installer files) fetched via
random access to SMB archive and cached for Add. Offline-image Add instead
attempts fresh installation and rejects available disk space, so it was
not allowed to replace the working shared installation. Firmware-only
build is PARTIAL, not deployable as a complete core-device package.

Configuration/reproducer: diagnostics/kasli-master/. Source revisions and
artifact hashes: evidence/kasli-v2.1-master-2026-10-08.json. Outputs in
build/kasli-v2.1-master-2026-10-08/generated/genesys_drtio_master.
Genesys remains running prior CoreDMA image; no hardware programming was
performed while preparing this Kasli build.

## 2026-10-09: shared Artix-7 support restored from SMB

Official installed-tree Vivado2025.2 `Add` completed offline with exit0,
without AMD authentication. Selected archives read from local cache; a
read-only FUSE view exposes the remaining real SMB tar entries for the
installer's all-Linux-archive presence check. No dummy archives or patched
installer. XC7A100T24 variants / XCZU5EV26 variants found; small synthesis
PASS for both Kasli v2.1 and Genesys ZU5EV. All threads retain the shared
Vivado launcher. Kintex-7 and other7-series families are not asserted.
Evidence: evidence/artix7-install-2026-10-09.json. Reproduction documented
in /home/codex-hil/docs/toolchains/vivado.md. Full Kasli master gateware
build resumed; timing closure/bitstream/hardware validation pending.

## 2026-10-09: Kasli v2.1 DRTIO master build PASS

Complete test-master package built from pinned upstream ARTIQ486e8f8:
bootloader, ksupport, runtime and gateware top.bit/top.bin. Vivado2025.2
synthesis/place/route/bitgen PASS; WNS0.141ns, WHS0.037ns, pulse width0.264ns,
zero violating endpoints and pre-bitgen DRC0 errors. Both .bit and .bin now
retained by the reproducible build script. Runtime FBI length/CRC32 and all
artifact hashes verified. Upstream OpenOCD+bscan-SPI built; artiq_flash
--dry-run PASS. No Kasli was programmed. Build-qualified test configuration
(no EEM,125MHz,WRPLL off), not a validated production/master-satellite link.
Inherited external I/O-delay / multiple-clock / unused SMA-clock warnings
are recorded in evidence/kasli-v2.1-master-2026-10-08.json for hardware and
constraint qualification. No unconstrained internal maximum-delay endpoint.
Package: build/kasli-v2.1-master-2026-10-08/kasli-v2.1-master-125mhz-artiq10-test.tar.gz.
Physical Kasli boot/Ethernet/DRTIO and Genesys satellite firmware remain pending.

## 2026-10-09: resumed DRTIO raw20 protocol integration

Genesys/Kasli USB connections are absent after host restart; no hardware
reset/programming was attempted. Existing completed Kasli v2.1 package and
physical GTH PRBS evidence are preserved. Raw20Codec reuses existing
MiSoC8b10b and ARTIQ ChannelInterface for future GTH integration. Three
wire-level simulations PASS against both Piotr's preserved ARTIQ and the
pinned current master snapshot: concurrent RT/AUX payloads with RX phase
offset, swapped-lane negative control and all16 ready/reset conditions.
Reproducer: make test-drtio-codec; evidence/drtio-raw20-codec-2026-10-09.json.
Codec is not yet connected to board diagnostic or satellite firmware.
GT alignment, Si5342 clock recovery, buffer bypass/deterministic latency,
remote link and auxiliary satellite firmware remain pending. Kasli1.1
board qualification was handed to a separate user-requested thread.

## 2026-10-09: Si5342 recovered RX clock — laboratory hardware milestone

| Subsystem | Piotr | Duke | Upstream reused | Current status | Test |
|---|---|---|---|---|---|
| PS I2C/Si5342 backup | Existing PS export reused; no board-clock driver reused | Not used | AMD XIicPs2025.2, Digilent mux protocol | DONE diagnostic | Two3072-register reads, identity/rev03 and12 page selectors verified |
| RX clock forwarding | Existing PS/Migen top extended locally | Not used | ODDRE1/OBUFDS/BUFGCTRL, Digilent clock pins | DONE diagnostic | Vivado timing/Gray CDC checks and physical IN0 LOS transition |
| Si5342 PLL lock | No clock profile reused from Piotr | Not used | Digilent generated DSPLL settings, Si5342 Rev-D register definitions | DONE laboratory; production integration PARTIAL | Independent PS125MHz lock, actual RXCLK lock, three loss/relock cycles |
| GTH under recovered-clock lock | Existing PHY diagnostic extended | Not used | AMD GTHE4 PRBS7 checker and user clocks | DONE internal loopback | Both TX/RX counters active, zero new settled PRBS errors after each reacquisition |
| Remote DRTIO clock/synchronization | Still pending | Not used | Existing ARTIQ protocol/PHY planned | MISSING hardware proof | Kasli/SFP link, deterministic latency, jitter and cross-board timing NOT_RUN |

The recovered user-clock target is nominal125MHz; the
GTH reference output remains156.25MHz. Profile P0=63/M=1386 gives a PFD
near1.984MHz and preserves the original13.75GHz VCO/N/R/output settings.
The profile is experimental, derived from the existing Digilent HDMI
configuration rather than certified by a new ClockBuilder Pro run. The
laboratory OOF window is widened; its absolute threshold and output jitter
are not independently measured. Self-loop lock does not establish an
accurate external time reference. Elastic buffers remain enabled.

`make test-hw-si5342` reproduces the clock test after the documented loader.
It saves/restores every touched volatile register and verifies real clock
activity/PRBS, not just ready flags. `make test-si5342` checks the frequency
plan and rejects the previously observed fractional-mode/clock-gate and
output-plan mistakes. No OTP/boot-flash writes or changes to original
source checkouts. See [Si5342 instructions](diagnostics/si5342/README.md).

Evidence: `evidence/si5342-readout-2026-10-09.json`,
`evidence/drtio-clock-forward-build-2026-10-09.json`, and final physical
clock/core-restore evidence recorded for this session.

Final restoration PASS: board DHCP address192.168.2.3, CPU1 ready,
ICMP3/3, normal `artiq_run examples/genesys_dma.py` produced eight physical
pulses/sixteen edges with the expected input timing. The previous local
ARTIQ integration runtime is running again; diagnostic PL is not left loaded.
Two complete clock-test sessions passed, six loss/relock cycles total.
Final evidence: `evidence/si5342-recovered-clock-2026-10-09.json` and
`evidence/si5342-restored-core-2026-10-09.json`.

## 2026-10-09 — upstream RT/AUX framing over physical GTH

The optional protocol diagnostic top integrates existing ARTIQ LinkLayerTX/RX
and MiSoC 8b/10b on actual GTH clocks. Three internal PMA loopback cycles
passed with zero new settled RT/AUX payload or frame-length errors. Each
cycle received more than 15,000 frames of each traffic type; deliberate raw
bit corruption produced over 60,000 receiver errors and clean recovery.
Alignment offsets varied after resets, demonstrating acquisition rather than
a fixed assumed word boundary. External SFP TX remains disabled.

Three simulations passed: all 20 aligner offsets, clean framed traffic and
encoded-bit corruption/recovery. Bitstream, timing, 318 first-stage CDC
register checks and nine Gray bus-skew checks PASS. Counter constraint
names were corrected after initial synthesis, then implementation resumed
from the preserved checkpoint. See diagnostics/drtio/README.md and
evidence/drtio-framing-hardware-2026-10-09.json.

This is link framing, not satellite packet execution, AUX firmware discovery
or deterministic latency. Elastic buffers and a fabric comma aligner remain
laboratory choices. Board temporarily runs diagnostic PL while the next
firmware clock-control stage is developed; normal runtime must be restored
after testing. No OTP/flash or other connected FPGA board was modified.

## 2026-10-09 — autonomous Si5342 diagnostic firmware

CPU0 firmware, using the maintained AMD XIicPs transport and validated
P0=63/M=1386 profile, independently bootstraps Si5342 from PS125MHz, resets
GTH, switches to RXCLK and monitors lock. Three physical one-second IN0
loss events each triggered PS fallback and RX reacquisition. All four
settled clock measurements passed with zero new PRBS7 errors. Saved volatile
registers were restored afterward; no OTP/flash. Evidence:
si5342-autoclock-hardware-2026-10-09.json. Firmware clock control PARTIAL:
autonomous diagnostic PASS; production satellite integration, time
synchronization, remote master and jitter remain NOT_RUN.

## 2026-10-09 — physical analyzer and MonInj PASS

| Subsystem | Existing work reused | Current status | Test |
|---|---|---|---|
| Analyzer | Upstream ARTIQ MessageEncoder, standard dump ABI/client | PARTIAL: local 256-record BRAM ring and network dump PASS; DDR-backed writer absent | Physical DMA dump37 records:16 output/16 input, stop; wrapped256-record TCP dump, reset/restart, native underflow record |
| MonInj | Existing ARTIQ gateware and CommMonInj client | DONE for the two local simple TTL channels; wider channel support and multiple clients pending | Probe subscriptions, injected high/low physically seen on JB1→JB2, readback, disconnect cleanup, invalid handshake rejection |

The normal runtime now uses `build-vivado/rtio-debug-fixed-2026-10-09/top.bit`,
CPU0 `build-vivado/debug-services-2026-10-09/amd/app/build/lwip_echo_server.elf`
and existing CPU1 `build/kernel-worker-dma-final`. DHCP192.168.2.3.
Standard analyzerTCP1382 and MonInjTCP1383 are active alongside management
1380 and kernels1381. Nine normal CoreDMA experiments validated72 pulses/
144 loopback edges. Native DMA errors mask255 and analyzer underflow record
passed additionally; management log retrieval still works.

FPGA timing WNS1.900ns/WHS0.016ns, checked42 first-stage CDC registers and
all existing CSR offsets/widths unchanged. BRAM wrap/stop/restart simulation
and AXI/local-RTIO regression PASS. Test runner fixes address the asynchronous
CommMonInj close/reconnect race and the actual `artiq_run --device-db` flag.
Initial build was superseded by the fixed output tree. A shell-script edit
during the fixed run interrupted only post-build verification; verification
was rerun explicitly against the completed bitstream and reports.

Evidence: rtio-debug-hardware-2026-10-09.json. Reproducer: docs/RTIO_DEBUG.md.
This finite BRAM prototype pauses capture briefly on retrieval, serves one
client per debug port and polls MonInj every500ms. It is not full upstream
analyzer DMA or production qualification. No other FPGA, OTP or flash write.

## 2026-10-09 — updated standalone SD image prepared

`build/sd-debug-2026-10-09/boot.bin` includes FSBL/PMU, the validated local
CoreDMA/analyzer/MonInj PL and CPU0 runtime, and the embedded CPU1 worker.
Packaging and partition-header checks PASS; source images physically
validated via JTAG. Card write and new-image cold boot NOT_RUN: the USB
reader/card is not present on the host and a physical power cycle requires
user assistance. Previous non-DMA SD image remains unchanged.
Evidence: sd-debug-package-2026-10-09.json. See docs/SD_BOOT.md.

## 2026-10-11 — encoded DRTIO packet and AUX simulation

Upstream master/satellite packet engines now have a port-local regression
through raw 20-bit 8b/10b codecs and comma alignment, rather than decoded
ideal wires. Echo response and scheduled TTL edge intervals PASS. AUX
Wishbone memory transfers, ring wrap, concurrent RT traffic, offset
acquisition, queue overflow and recovery PASS. Four new tests, all bounded.
Original upstream/submodule code remains unchanged.

Status: packet integration PARTIAL (simulation PASS); physical satellite
packet execution, AUX firmware discovery/routing and external master
synchronization NOT_RUN. This does not upgrade physical framing results
into packet-layer hardware results. Working normal core was not reset or
reprogrammed. Reproducer: `make test-drtio-raw-packets`; evidence:
`evidence/drtio-packets-simulation-2026-10-11.json`.

## 2026-10-11 — time-slotted physical packet diagnostic prepared

Six packet-probe/regression simulations PASS. Upstream master/satellite RT
packet engines are connected to one raw20 codec, with time slots and an
asynchronous reply FIFO so each request and reply can traverse the same
physical GTH loopback. The backend checks CRI fields and synthesizes replies;
it does not execute local RTIO/SED. Echo, set_time, extended writes,
buffer-space replies, read/event/timeout/overflow, dropped-reply timeout,
unknown-type and truncated-header errors plus clean recovery simulated.

The original satellite truncation guard is unreachable in both pinned and
archived modern ARTIQ; a guarded local subclass corrects its nesting without
editing original sources. Tiny negative-control tests PASS on both snapshots.
A test also caught diagnostic timeout loss when disabling the generator;
request-based arming fixes it. See docs/DRTIO_PACKET_TRUNCATION.md and
new simulation evidence. Current FPGA build/hardware validation in progress;
this section alone is not hardware evidence.

## 2026-10-11 — physical RT request/reply packets PASS

| Subsystem | Current status | Physical acceptance |
|---|---|---|
| RT packet serialization/parsing | PARTIAL: diagnostic physical request/reply path PASS; production satellite absent | 36 cases,36,239 requests across three GTH resets, exact drained-counter conservation |
| Satellite command backend | STUB for RTIO execution: deliberately checked diagnostic CRI responder | set_time; channel/address/timestamp and extended512-bit write payload; buffer space; read data/timestamp, timeout and overflow |
| Error handling | DONE for diagnostic cases | Exactly one error/result per deliberately suppressed reply, CRI buffer timeout, unknown type and truncated header; clean echo recovery |
| AUX | PARTIAL: prior framing hardware and controller simulation PASS | CPU AUX protocol/discovery/routing hardware still NOT_RUN |
| External master and deterministic PHY latency | MISSING integration/qualification | SFP/Kasli link, synchronized RTIO/SED and GT buffer bypass still NOT_RUN |

Both directions use the same actual GTHE4/PMA loopback, with a laboratory
half-duplex slot scheduler and asynchronous reply FIFO. It is not a normal
full-duplex DRTIO topology and not a working production satellite. The CRI
backend does not drive TTL/SED. Separate native unknown/truncation/buffer
error counters establish which path fired. Positive traffic has zero new
satellite/master/FIFO errors. Each required result count exactly matches
sent requests after generation stops and pending slots drain. Sequential
DAP reads while traffic runs were superseded by this coherent acceptance.

Build: build-vivado/drtio-packets-armed-2026-10-11, bit SHA-256
12ae72ea4c027a45b244919e92e81ce1f8e7f84c27324346a577263911a6683b.
WNS2.641ns/WHS0.012ns, exact604 first-stage CDC bits and19 Gray bus-skew
constraints PASS. Existing PRBS7/clock-activity/mismatch/recovery also PASS
on this bitstream. Earlier builds were stopped as simulation/review exposed
missing diagnostics and the timeout-arm bug; final top-level was rebuilt
using official unchanged PS/GTH IP cache. Original checkout code untouched.

Two complete volatile load/test/restore sessions PASS; the second is the
exact-counter acceptance run. Normal CoreDMA/analyzer/MonInj PL and both
CPU images restored, DHCP192.168.2.3. Both restoration suites passed nine
normal DMA experiments (72 pulses/144 loopback edges), analyzer256-record
wrap/restart and MonInj physical loopback/injection/cleanup. GEM tests passed
20/20 ICMP and five byte-exact TCP echo connections per session. External
SFP TX remained disabled; no Si5342, SD/flash/OTP or other FPGA writes.

Evidence: evidence/drtio-packets-hardware-2026-10-11.json. Reproducer:
diagnostics/drtio/README.md, scripts/test_drtio_packets_bringup.py. Shared
Genesys flock held through reset/programming/tests/restoration. Remaining
next work: AUX controller/firmware, production satellite RTIO/SED wiring,
clock-manager integration and external Kasli synchronization.

## 2026-10-11 — PS/GTH AUX clock crossing

The next AUX integration preserves the upstream SRAM controller and moves
only its TX stream across clocks using a whole-packet asynchronous FIFO.
The controller/Wishbone remain on the PS clock; TX link uses the GTH clock
and RX retains its upstream recovered-clock memory writer. No original
ARTIQ/Migen sources were changed. See diagnostics/drtio/AUX_CDC.md.

Unrelated-clock simulation exposed a false first RX packet before
scrambler convergence. A 127-cycle recovered-clock startup quarantine fixes
that issue. Ring wrap, overflow/recovery and RT arbitration use the actual
upstream AUX controller, link layer and raw20 codec in these tests.

Status remains PARTIAL: this endpoint is not yet in the physical diagnostic
top-level. AXI decode/CSR mapping, additional CDC constraints, coordinated
reset integration, Vivado build and physical AUX/firmware tests remain
NOT_RUN. This step does not reset/program the Genesys or modify its running
local CoreDMA/analyzer/MonInj image. Firmware must wait for bridge drain in
addition to the upstream TX enqueue-busy flag. Independent GT reset while
the PS bridge runs is not supported yet.

Acceptance: `make test-drtio-aux-cdc` — five tests PASS. This includes the
maximum 1024-byte packet through upstream TX/RX SRAM and raw20 framing,
not only FIFO token testing. Evidence:
evidence/aux-cdc-simulation-2026-10-11.json (source/log SHA-256 recorded).

## 2026-10-11 — AUX bus decode and AXI error propagation

Offline integration components now reserve relative CSR0x00000–0x03fff and
AUX SRAM0x10000–0x13fff without high-address truncation aliases. Two bus
simulation tests PASS, including actual upstream AUX SRAM TX word
readback and RX window selection. No physical transactions were issued.

Inspection found that installed LiteX AXILite2Wishbone ignores ERR and
always returns OKAY. A checked local overlay reuses its FSM, terminates on
ACK or ERR and latches SLVERR. Read/write negative controls, response
backpressure and error-to-success recovery PASS (one additional test).
Upstream LiteX remains unchanged. Full AXI conversion/PS validation and
physical diagnostic top-level/CSR/reset/CDC integration remain NOT_RUN.
Evidence: evidence/aux-bus-simulation-2026-10-11.json. No board access,
reset/programming, persistent writes or running-runtime changes this turn.

## 2026-10-11 — standalone full-AXI AUX integration

AuxPS now joins full AXI conversion, the error-aware LiteX bridge, CSR/SRAM
routing and retained upstream AUX endpoint. Bank3 exposes AUX control and
RX ring registers plus bridge_busy/rx_up/in_reset. Private PS/TX/RX endpoint
domains share a reset input with FPGA reset synchronizers; enclosing physical
top-level must drive PS reset OR GT reset/not-ready. Transport stays alive.

One full AXI simulation test PASS: IDs/last, SRAM first/last word, CSR
length, SLVERR/no high-address alias, recovery and functional reset. It
caught two issues: aligned MiSoC CSR readback write68/read512 and CSRBank
ownership keeping the length register outside endpoint reset. Both fixed
locally; preserved dependencies unchanged. Simulation reset override is
functional only; hardware reset timing/active-transfer recovery NOT_RUN.

Standalone HDL with complete AXI/raw20/clock ports and map generated PASS.
This is not synthesis or hardware acceptance. Physical top-level embedding,
CDC/timing constraints, Vivado build and firmware AUX still pending. No HW
access this turn. Evidence: evidence/aux-ps-integration-2026-10-11.json.

## 2026-10-11 — Genesys AUX top-level HDL generation

Diagnostic --aux now embeds the full-AXI AUX block in Piotr's existing
Genesys PS/GTH platform. Existing monitor bank0 remains accessible; bank3
and 16 KiB AUX SRAM map are exported. Reset includes PS/monitor reset and
GT TX/RX PMA/done/active loss. External SFP TX defaults disabled.

HDL/map generation PASS using the preserved PS export and existing156.25 MHz
GTH IP. Generated exact153 first-stage synchronizer bits and five Gray
bus-skew constraints (three counters plus two13-bit FIFO pointers). These
are pre-synthesis counts, not Vivado retained-cell or timing acceptance.
Full AXI extra-monitor-bank simulation PASS; shell/Python syntax checks PASS.
Build wrapper now supports DRTIO_AUX=1 and checker requires five skew results.
Vivado synthesis/route and physical AUX/active-transfer reset remain NOT_RUN.
No hardware access. Evidence: evidence/aux-top-generation-2026-10-11.json.

## 2026-10-11 — AUX diagnostic Vivado build PASS

Physical Genesys AUX top-level synthesized, placed, routed and generated a
bitstream successfully with shared Vivado2025.2. Existing PS/GTH IP cache
reused. Exact153 retained first-stage synchronizer bits and five Gray
bus-skew constraints PASS. Timing closed: WNS2.696ns, WHS0.011ns, no failing
setup/hold endpoints. Build checker and artifact hashes PASS.

Build: build-vivado/drtio-aux-route-2026-10-11. Bit SHA-256:
c54dcb6e82f9d45b658de4762926ef75f18831242b9b3ad0ad40391b8aabdfc9.
Evidence: evidence/aux-vivado-build-2026-10-11.json. Source/dependency
manifest and all reports/logs retained in the build directory.

Full AXI functional reset simulation now aborts a1024-byte packet during
CDC enqueue, verifies cleared TX/bridge/length state, and successfully
sends a fresh packet after reset. PASS; this does not qualify physical
reset timing, stopped-clock reset or exact RX payload recovery.

No hardware access/programming/restoration this turn. Physical AUX remains
NOT_RUN. Next bounded acceptance is documented in
 diagnostics/drtio/AUX_HARDWARE_ACCEPTANCE.md: locked load/test/restore,
patterned SRAM/packet/ring/error/reset checks and normal-core regression.
Firmware AUX protocol/discovery/routing and external Kasli remain pending.

## 2026-10-11 — physical AUX controller/memory PASS

The routed AUX image passed the bounded physical Genesys test under the
shared board lock. Upstream AUX controller SRAM, independent PS/TX/RX
clocks, raw20/8b10b framing and actual GTHE4 PMA loopback participated.
Three GT resets,30 positive packets of4/12/68/1024 bytes (six maximum-sized),
ring pointer wrap and exact payload comparison PASS. Three deliberate
ring-overflow controls preserve seven readable packets, clear the flag and
successfully receive fresh packets.57 total sends,54 receives checked;
three deliberate discards,1704 payload words checked exactly. Length CSR
readback, GT/PRBS clock/error baseline and recovery PASS.

No firmware AUX protocol/CRC/discovery/routing is claimed. Active-transfer
physical reset remains NOT_RUN: sequential JTAG accesses cannot prove the
reset landed during a microsecond transmission. Functional RTL enqueue-abort
coverage remains distinct. External SFP TX disabled; no Si/SD/flash/OTP or
other board writes. Evidence: evidence/aux-hardware-2026-10-11.json.

Wrapper scripts/test_drtio_aux_bringup.py held the shared Genesys lease over
load/PHY/AUX/restore and normal-core regressions; released after129.218s.
Normal rtio-debug-fixed PL, debug-services CPU0 and kernel-worker-dma-final
CPU1 restored, DHCP192.168.2.3. Standard physical TTL/CoreDMA/debug tests
PASS; analyzer ring wrap/restart and MonInj PASS; Ethernet20/20 ICMP and
five TCP connections/1080 exchanges/1129210 exact bytes PASS. AUX firmware
handling is the next independent stage; remote Kasli remains NOT_RUN.

## 2026-10-11 — upstream Rust AUX codec in physical A53 firmware PASS

Unchanged current ARTIQ drtioaux_proto/libio and CRC library are linked into
a no_std AArch64 static library, with a small C ABI/envelope wrapper. AMD BSP
C harness provides MMIO/UART and two laboratory AUX roles on CPU0. No
upstream source modification or rewritten packet enum/serializer. Locked
Rust dependencies retained; existing Rust1.87/GNUArm13.2/AMD BSP used.
libio never_type uses scoped RUSTC_BOOTSTRAP. Host compatibility required an
explicit extern crate core for the old derive; original sources untouched.

Actual Piotr and current upstream host codecs generate identical seven
basic wire vectors; roundtrip/CRC/truncation/unknown controls PASS. This
comparison is limited to those basic packets, not all modern AUX variants.

Physical firmware PASS:31 request/reply exchanges using the actual GTH PMA
loopback, corrupted CRC rejection, unknown type rejection and echo recovery.
Requests cover echo, laboratory reset acknowledgement and destination status.
Destination replies DOWN because satellite RTIO is absent; ResetAck does not
imply production RTIO reset. Firmware idles after its bounded self-test;
there is no persistent autonomous AUX service or remote discovery yet.

AUX SRAM/PHY tests also repeated PASS. Shared Genesys flock covered139.957s
load/test/restore. Normal local core restored192.168.2.3; physical TTL/CoreDMA,
standard analyzer/MonInj ring-wrap/restart and Ethernet20/20 ICMP/five TCP
connections PASS. No Si/SD/flash/OTP or other board writes. Firmware ELF
SHA e1414739dea3b4707597a0c919ce4d9fc0e50d17d0c77fcee605c0cf44d955b0.
Evidence: evidence/aux-codec-reference-2026-10-11.json and
 evidence/aux-firmware-hardware-2026-10-11.json. Reproducer:
diagnostics/drtio/aux_protocol/README.md. Next work is a persistent handler,
TSC/control integration and real satellite RTIO/SED; remote Kasli NOT_RUN.

## 2026-10-11 — persistent minimal AUX responder PASS

After its original31-pair self-test, firmware now stays in a receive/dispatch
loop. Echo receives EchoReply; destination queries receive DOWN. Replies are
consumed without another response, preventing PMA-loopback storms. Malformed
CRC and unknown packets are dropped. Persistent ResetRequest is explicitly
unsupported and dropped until a real RTIO backend exists; the prior bounded
self-test's laboratory ResetAck remains separate.

Physical persistent service PASS:18 UART-injected AUX requests across three
rounds, nine response packets and nine ignored loopback replies, three each
bad-CRC/unknown/unsupported-reset drops, echo recovery after every set. Exact
UART event counts and no RX/SEND errors. All traffic traverses physical GTH,
but injector and responder share one A53. No remote Kasli, production
satellite RTIO/SED/TSC/reset or routing claim. Unchanged upstream Rust
codec/CRC and the previously routed AUX PL retained.

AUX memory/PHY and original firmware self-test repeated PASS. Shared lock
covered168.681s load/test/restoration. Normal local core restored192.168.2.3;
physical TTL/CoreDMA, standard analyzer/MonInj and Ethernet PASS. No Si/SD/
flash/OTP or other board writes. Evidence:
evidence/aux-service-hardware-2026-10-11.json. Reproducer: bounded AUX wrapper
--firmware ELF --service-test. Next offline step: connect retained upstream
satellite packet/CRI path to real RTIO/SED, with simulation before hardware.

### 2026-10-11 — real satellite SED simulation

PASS: retained upstream master packet serialization → checked satellite parser
→ actual SyncRTIO/SED → TTL PHY; four scheduled writes, exact four output
strobes/edges, preserved 32-clock intervals and no asynchronous SED errors.
Disconnected-frame negative control PASS with no strobes/edges. Uncompensated
latency is nine clocks to PHY strobe plus two to TTL: timestamp compensation
is still pending. Two output channels/eight SED lanes used to avoid retained
Migen zero-width address/counter elaboration failures. No original source or
hardware modified. Ideal single-clock packet wiring only; no physical DRTIO
satellite or remote synchronization claim. Reproducer and scope:
diagnostics/drtio/SATELLITE_SED.md; make test-drtio-satellite-sed.
Next: validate timestamp compensation, TSC load and error recovery offline,
then integrate the real backend into the physical diagnostic.

### 2026-10-11 — satellite time-load and underflow recovery simulation

Five satellite SED tests PASS. Serialized set_time loads counter1000 exactly
once and subsequent timestamped TTL events execute. A stale timestamp10 write
raises native CRI underflow, produces no output, and four later valid writes
execute with no extra strobes/edges. Diagnostic sender advance11 yields edges
at requested counter values; production master/SED semantics remain unchanged.
No GTH/CDC/external-clock proof or hardware access in this stage. Reproducer:
make test-drtio-satellite-sed; scope in diagnostics/drtio/SATELLITE_SED.md.
Next safe offline step: read/input and real buffer-space replies, then refactor
the tested backend for physical GTH diagnostic integration.

### 2026-10-11 — real satellite buffer-space and input reads

Seven satellite SED simulation tests PASS. Serialized buffer-space replies from
actual SED FIFOs are128→124→128 around four queued/executed writes. Upstream TTL
input PHY and InputCollector capture one simulated loopback rising event at253;
serialized read returns exact data1/timestamp253. Subsequent empty read returns
native timeout without overflow. Event-response overflow field is unspecified
by upstream and intentionally ignored. No packet parsing/buffer timeout errors.
No hardware access or physical input/synchronization claim. Evidence:
evidence/satellite-sed-io-simulation-2026-10-11.json; same Make reproducer.
Next safe step: extract reusable real satellite backend and connect it to the
existing physical GTH diagnostic, retaining bounded reset/test/restoration.

### 2026-10-13 — reusable satellite backend

Extracted SatelliteBackend with retained upstream TSC/SyncRTIO/TTL and checked
packet parser. All seven packet/SED/input/capacity/time/error simulations PASS
using the extracted module. Standalone Verilog generation PASS, artifacts in
build/satellite-backend-2026-10-13 on the data volume. No FPGA synthesis/routing
or hardware access performed. All domains deliberately map to sys; caller must
provide synchronous words or verified crossing. Production satellite reset/AUX
ResetRequest remains unsupported. Next step is lab GTH transport/common-reset
integration and simulation before routing and bounded physical validation.

### 2026-10-13 — KASLI03 handoff accepted

User handed over KASLI03 for master/Genesys integration and reports Kasli
loopback removed. Read rng-rpi's board-specific handoff. Read-only JTAG identity
PASS under KASLI01/02/03 shared locks: DNA0048458a64b04854, USB001:077,
topology1-6.2; raw logs copied to evidence/kasli03-handoff-2026-10-13.
No programming/reset/UART/network/clock writes performed; locks released.
Separate v1.1 master125MHz configuration added; build started on pinned current
ARTIQ, completion pending. Earlier v2.1 artifacts are incompatible and excluded.
Exact Kasli SFP downstream port awaiting operator clarification. Before SRAM
deployment, prepare RAM-only firmware boot: upstream bootloader tries flash
first. No flash modification authorized or performed. See diagnostics/
kasli-master/KASLI03.md. Remote Genesys transport integration remains pending.

### 2026-10-13 — Kasli1.1 master build and RAM-only preparation

Original pinned master build PASS: bit/bootloader/runtime complete,
WNS0.001/WHS0.061/pulse0.264ns, no violating endpoints; hardware NOT_RUN.
Evidence kasli-v11-master-build-2026-10-13.json. Narrow setup margin and inherited
external constraint warnings retained as limits. This flash-first image not loaded.
Prepared checked separate netboot-only source worktree, preserving upstream:
flash boot disabled, unique KASLI03 lab MAC02:4b:03:48:48:54/DHCP, no static
address/routes from persistent configuration. Reviewable overlay committed.
Initial shadowed-None compile failure fixed; netboot build restarted and ongoing.
No hardware access or storage/clock changes. Next: qualify netboot artifacts,
then bounded identified SRAM boot/network test with clock restoration addressed.

### 2026-10-13 — durable netboot build and bounded boot acceptance prepared

Netboot firmware compilation PASS. Previous FPGA build stopped during synthesis
without completion evidence; do not treat it as routed. Restarted in user
systemd service artiq-kasli03-netboot-20261013 with frozen script snapshot and
persistent log; no device access or locks held. Prepared KASLI03 bootloader-only
wrapper requiring reviewed netboot qualification/hash, exact DNA, shared Kasli
locks, UART CRC/DDR/netboot evidence and finally guarded diagnostic restoration
with bounded CSR verification. Wrapper hardware NOT_RUN; image still pending
routing. Bootloader stage does not upload runtime or initialize Si5324 via
runtime. Next: finish/qualify image, preflight wrapper, bounded bootloader test.

### 2026-10-13 — netboot network policy corrected during route wait

Inspected actual upstream network_boot: no DHCP client. Its use_dhcp console
field is configuration, not an acquired IPv4 address. Netboot-only image has
IPv6 link-local fe80::4b:3ff:fe48:4854/TCP4269; host interface scope and network
acceptance pending. Startup wrapper additionally requires Waiting for connections
and records DHCP not implemented. Raw runtime.bin is the protocol payload,
not runtime.fbi. No hardware access. Netboot routing still running; next safe
step is build acceptance followed by bounded bootloader SRAM test.

Netboot build qualifier added: checked overlay/revision, source selection,
config/part, timing/DRC, completion and artifact hashes. Original flash-first
build negative control rejected as expected; no qualification JSON generated.
Positive netboot acceptance pending current routing. No hardware access.

### 2026-10-13 — failed KASLI03 netboot deployment, restored diagnostic

Original qualification WITHDRAWN: compiler/source checks missed absent embedded
ROM. Standard Kasli CPU reset0x400000 fetched old flash bootloader/ARTIQ8 instead
of newly compiled netboot firmware. UART shows original bootloader DDR PASS,
old runtime VOR2309003 and volatile Si5324 internal125MHz initialization/lock.
Netboot-only hardware test FAIL; full-checker restored and CSR identity/EEM0/
GTP0/SFPdisable7 PASS. Shared three Kasli locks held across test/restoration;
Genesys untouched. No flash programming commands; content recheck NOT_RUN.
Exact original Si5324 register restoration NOT_PROVEN. Raw evidence:
evidence/kasli03-netboot-hardware-2026-10-13. Earlier clock_written=false field
corrected from actual console evidence; do not claim unchanged clocks.

Corrected overlay removes flash boot code, uses integrated128KiB ROM/reset0
and initializes ROM from ARTIQ bootloader.bin rather than generic MiSoC BIOS.
Manifest records embedded hash/size/reset; qualifier/wrapper now require it.
Old image negative control rejected. Corrected isolated worktree and durable
build started; physical corrected image NOT_RUN. Next safe step: qualify actual
embedded ROM and timing, repeat bounded bootloader-only test.

Corrected integrated-ROM build initially failed because upstream runtime assumes
SPI flash imports/reload/address even with no flash core. For the next bounded
boot-only acceptance, build explicitly contains bootloader only; no runtime
artifact claim. Compiled bootloader and actual ROM initialization PASS/reset0;
evidence kasli03-bram-initialization-2026-10-13.json. Durable FPGA build restarted,
routing pending. Prior netboot build evidence marked WITHDRAWN. No further HW
access after diagnostic restoration; runtime flash-free support remains pending.

### 2026-10-13 — KASLI03 BRAM boot hardware PASS; flash-free runtime compile PASS

BRAM bit SHA4fb33ce8..., WNS0.092/WHS0.051/pulse0.264ns. Actual ROM words
match compiled bootloader; generated reset0/ROM wiring verified. Physical boot
CRC/DDR initialization/memory test, disabled flash boot, forced MAC and listener
startup PASS. First automated run false-negative on MAC separators; fixed and
full repeated test PASS. Both restores full-checker CSR identity/EEM0/GTP0/
SFPdisable7 PASS under all three Kasli shared locks. No runtime upload, old flash
runtime or observed Si5324 setup in these corrected runs; Genesys untouched.
Raw logs evidence/kasli03-bram-netboot-hardware-2026-10-13. Network connections
and remote DRTIO NOT_RUN; prior first-image clock caveat remains historical.

Separate checked flash-free runtime overlay compiles bootloader/ksupport/runtime
PASS. Guards SPI imports/functions; no-flash flash/reboot return Error, panic
halts, config uses upstream NoFlash. mem.rs/csr.rs/regions.ld byte-identical to
physical BRAM image. Runtime hardware NOT_RUN; build evidence committed. Next
safe work: scoped IPv6 netboot connection and bounded clock capture/restoration
before uploading runtime; external satellite integration still pending.

### 2026-10-13 — IPv6 netboot negative/recovery test prepared

Extended bounded Kasli boot wrapper with optional interface-scoped TCP4269:
unknown command and boot-without-firmware rejection checked against UART,
fresh listener connection recovery and exact IPv6 neighbor MAC. No payload
upload/runtime/clock writes in this scope. Host IPv6 preflight before any HW.
Physical network test NOT_RUN: enp1s0 currently has no IPv6 address, sudo requires
password; requested explicit temporary link-local address from operator.
No privilege bypass, network mutation or new hardware access performed.
Safe independent continuation: satellite GTH/CDC and runtime clock restoration
preparation while host address is unavailable.

### 2026-10-13 — KASLI03 IPv6 netboot network hardware PASS

Operator provided enp1s0 link-local address. Scoped TCP4269 three connections,
unknown-command and boot-without-firmware rejection with exact UART evidence,
listener recovery and neighbor MAC02:4b:03:48:48:54 PASS. Boot CRC/DDR repeated
PASS. No runtime upload/execute, flash command, Genesys access or observed Si5324
setup. Shared three-Kasli locks held through full-checker restore/CSR PASS.
Raw evidence/kasli03-netboot-network-2026-10-13. Host temporary link-local retained.
Next safe step: bounded RAM firmware download without execution. Later runtime
clock initialization/sys switch may reboot to BRAM loader and need re-upload;
clock snapshot/restoration must be addressed before that execution step.

### 2026-10-13 — KASLI03 RAM firmware download hardware PASS

Uploaded1752788 bytes reviewed flash-free runtime.bin through native IPv6
netboot F/length/payload/OK; upstream UART reports completed download. No B
command or runtime execution, flash command, observed Si5324 setup or Genesys
access. RAM readback/checksum NOT_RUN; no independent byte-exact memory claim.
Boot/DDR/network negative/recovery and guarded full-checker CSR restore PASS
under all three shared Kasli locks. Evidence kasli03-netboot-download-2026-10-13.
Connection closure resets upstream downloaded flag; future execution requires
same-connection re-download/B after clock capture/restoration preparation.

### 2026-10-13 — KASLI03 Si5324 snapshot acquired

27 registers, two identical reads each, ID0182/PLLlocked: acquisition PASS.
Seven transient NACKs retried; I2C reliability PARTIAL. Shared three-Kasli locks
41.551s; no clock configuration/FPGA/flash writes. Original mux/bus CSR restored.
Decoded dividers match actual current ARTIQ Int125 profile exactly (including
both output dividers, CKIN2/free-run/BWSEL). No independent frequency/jitter or
restoration-sequence claim; snapshot covers driver-touched registers only.
Evidence kasli03-clock-snapshot-2026-10-13. Runtime remains NOT_RUN; next safe
step is hard-reset/sys-clock-switch and bounded restoration preparation.

### 2026-10-14 — clock/reset plan validated offline

Generated cfg confirms Si5324 soft reset, not GPIO hard reset. Checked snapshot/
driver plan covers23 configuration registers; excludes status/ID/136 commands,
requires deliberate calibration/readback/PLL/frequency and bus restoration.
Unstable duplicate-read negative control rejected/no plan emitted. Physical
restoration sequence still NOT_RUN. Runtime sys-switch/reboot to BRAM and
second upload flow documented but NOT_RUN. Runtime enables downstream TX:
all future execute sessions must also lease Genesys because of user's cable.
No hardware access this stage; evidence kasli03-clock-restore-plan-2026-10-14.
Next safe step: implement/test bounded baseline-profile restoration, then
controlled runtime startup under both boards' shared locks.

### 2026-10-14 — historical I2C hardware/firmware findings

Found primary Kasli issue46 (2019) on pullup strength, repeaters and low-level
margins, with maintainer-reported changes implemented. Exact board revision and
onboard Si5324 applicability unresolved; no claim this explains KASLI03 NACKs.
Upstream2020 driver fixed open-drain/phase handling;2018/2025 Si5324 reset-value
NACK special case does not match our read address/offset failures. Diagnostic
uses its own UART-side Python bitbang, so firmware-vs-hardware remains open.
References and exact commits in diagnostics/kasli-master/I2C_HISTORY.md.
No HW access; next safe step compare ACK timing and trace relevant schematics.

### 2026-10-14 — settled diagnostic I2C first hardware run PASS

54 reads/27 register pairs, zero NACK/retry, exact prior snapshot match/PLLlocked.
Timing overlay separates SCL falling from SDA changes, holds100us and samples
late. Earlier original run had seven retried NACKs; causal attribution remains
NOT_PROVEN pending fresh interleaved controls. Two delayed-ACK/true-NACK offline
controls PASS. Shared three-Kasli lease79.554s; routing restored, no clock data/
FPGA/flash/Genesys changes. Evidence kasli03-clock-settled-2026-10-14.
Next safe step: fresh original-vs-settled repeat, then bounded profile restoration.

### Continuation — fresh I2C A/B blocked before device access

Expected KASLI03 USB1-6.2 and UART disappeared. Original-timing capture aborted
before JTAG/UART/I2C; shared locks released. Host metadata inventory shows
Genesys and another FT4232H on historical KASLI01 path; no substitute access.
No new I2C measurements/configuration changes. Capture distinguishes absent
hardware from I2C failure. User clarification/reconnection needed; last settled
54 reads/zero-NACK result remains a single run, not causal proof.

### 2026-10-15 — KASLI03 returned; fresh I2C comparison

DNA0048458a64b04854 confirmed on USB1-2.4.1/001:019, UART channelC new hub path.
Wrappers support explicit location and UART-to-USB identity check. Fresh54-read
original run13 retried NACKs; subsequent54-read settled run zero. All values
identical/PLLlocked, mux/bus restored; no clock/FPGA/flash/Genesys writes.
Three shared Kasli locks covered each bounded session44.26/79.557s. Supports
timing-sensitive diagnostic behavior, not proof excluding electrical margins.
Evidence kasli03-clock-ab-2026-10-15. Next safe step: bounded profile restoration
using settled diagnostic reads, followed by cross-board-locked runtime startup.

### 2026-10-15 — KASLI03 volatile clock reset/restore hardware PASS

Under three Kasli locks149.249s, fresh baseline/disabled EEM/GTP/SFP verified;
soft reset136/0x80 produced expected value NACK;23 config registers restored,
fresh ICAL136/0x40, settled command bits/PLLlock, exact config/ID readback PASS.
No ordinary read/write retries. Diagnostic counter/host-time125.51–125.54MHz
within coarse ±1% nominal125MHz criterion; no ppm/jitter/phase qualification.
Mux/bus restored; no FPGA/flash/OTP/runtime/Genesys action. Two offline controls
PASS including rejecting config NACK and bounded recovery without repeated reset.
Evidence kasli03-clock-restore-2026-10-15. Runtime execution remains next stage,
with all connected-device locks, profile restoration and reboot/re-download.

### 2026-10-15 — current KASLI03 ARTIQ10 runtime starts from RAM: hardware PASS

Native netboot upload/B twice: first runtime initializes Si5324 and switches
sys clock/reboots to BRAM; second skips setup and starts matching current
ARTIQ10. UART management-active/accepting-network-sessions observed. No flash
commands/original flash runtime. Standard management client/kernel/remote DRTIO
still NOT_RUN. Two offline startup/reboot/panic controls PASS.

Shared Genesys+three Kasli locks held through load/UART/network/downstream TX
and restoration. No Genesys programming/configuration writes. Full-checker
CSR/disabled EEM/GTP/SFP restored PASS, then23-register clock baseline restore,
calibration/PLL/readback/nominal125MHz ±1% PASS and mux/bus restore. Volatile
Si writes explicit; no flash/OTP. Evidence kasli03-runtime-startup-2026-10-15.
Next safe step: repeat controlled startup with standard management queries
and then a simple local ARTIQ experiment, retaining cross-board leases/restore.

### 2026-10-15 — standard KASLI03 management hardware PASS

Two unmodified artiq_coremgmt log IPv6 connections PASS1909/2000 characters,
matching runtime ID and management/session startup evidence. Repeated RAM
startup/reboot/re-upload PASS. Cross-board locks retained through standard
client subprocesses and diagnostic/23-register-clock restoration PASS.
No flash/OTP; raw evidence kasli03-management-2026-10-15.

Simple local counter/wait/scalar-RPC example compiled rv32ima ELF32/RISC-V,
hardware NOT_RUN. NAC3 global delay name resolution fixed using core.delay.
Next safe step run experiment with actual scoped core address, retaining all
connected-board locks and restoration. Remote DRTIO remains NOT_RUN.

### 2026-10-15 — KASLI03 standard local kernel and RPC hardware PASS

Two standard artiq_run invocations compiled/uploaded/executed the rv32ima
counter probe over scoped IPv6. RTIO counter intervals1124392/1124776mu
exceeded the requested1000000mu wait; synchronous host RPC returned the
asserted0x12345678 value. No TTL writes. Standard coremgmt log also PASS twice.
This validates local kernel loading/execution, timeline wait and scalar RPC;
external DRTIO/AUX/discovery/TSC/remote TTL remain NOT_RUN.

Shared Genesys+three Kasli locks covered BRAM load, two-stage RAM startup,
clients and full-checker/23-register-clock restoration PASS. No Genesys
configuration, flash or OTP writes. Evidence kasli03-counter-2026-10-15.
Next safe step: prepare bounded external-link observation using both board
leases and reviewed Genesys diagnostic restoration before remote protocol tests.

### 2026-10-15 — external-link receive observer RTL simulation PASS

Existing ProtocolProbe checks a synthetic payload and cannot judge arbitrary
Kasli payload correctness. Separate LinkObserver uses unchanged raw20 codec,
comma aligner/upstream RX and four Gray counters, without a connected TX.
Twenty serial offsets PASS: exact arbitrary RT5/AUX4 words, one frame each,
disabled acquisition/counting and asynchronous management-clock visibility.
One test method/20 subcases,168.729s. Evidence link-observer-simulation-2026-10-15.
No hardware access. Not CRC/symbol-validity/link-up/synchronization proof.

External-link procedure diagnostics/drtio/EXTERNAL_LINK.md records required
both-board leases, RX-only first stage and full restoration. Integration into
diagnostic top, exact CDC/Gray constraints, timing-qualified bitstream and
bounded hardware wrapper remain next steps. The aligner must reset on lost
readiness before external use. External Kasli DRTIO remains NOT_RUN.

### 2026-10-15 — external observer top HDL/preflight PASS; route pending

Independent --observer/DRTIO_OBSERVER mode integrated in diagnostic top:
CSR bank3, external RX/PRBS-off defaults, hardwired optical TX disable and
zero TX data. Dedicated observer_rx domain resets alignment/counts on PS/
monitor reset or lost RX PMA/resetdone/active. LOS-only recovery requires
host monitor reset and discarded acquisition counts. RX reset/reacquisition
simulation PASS8.461s. Generated HDL structural checks PASS252 CDC bits/
seven Gray buses with exact synthesis guards. Not hardware evidence.

Initial route attempt withdrawn/stopped: CSRStorage.storage.reset did not
change actual storage_full reset values. Fixed, regenerated and verified
actual HDL defaults. Corrected build running in
build-vivado/drtio-observer-route-fixed-2026-10-15; route/timing/bitstream
acceptance remains PENDING. Evidence link-observer-top-preflight-2026-10-15.
No board/UART/network/reset/Si/flash/SD/OTP actions. Next: inspect corrected
Vivado result, address any timing/CDC issues, then bounded external RX wrapper.

### 2026-10-15 — observer bitstream BUILD_PASS

Corrected observer Vivado implementation/bitstream PASS; WNS2.770ns,
WHS0.002ns,252 retained first-stage synchronizer bits and seven passing
Gray-bus skew constraints. Optical TX hard-disabled in HDL; external RX/
PRBS-off reset defaults checked. Artifact SHA25663cc40e7e3ee1cba153aef8a96d0c61be9af1355b63099c58cb3f3eaf5f1a59a.
Evidence link-observer-top-build-2026-10-15.json. Build alone is not remote
link or deterministic-latency acceptance; hold slack is positive but small.

### 2026-10-15 — physical external KASLI03→Genesys RX clock/comma observed

Reviewed observer bitstream loaded under shared Genesys+three Kasli leases;
KASLI03 DNA0048458a64b04854 verified, current ARTIQ10 RAM startup, management
and two local counter/RPC experiments PASS. Four external snapshots show
status255 (PHY ready/module present/no LOS), alignment31 (aligned, offset15),
and RX/PS clock ratios near1.00002. RT/AUX word/frame counts all zero.
Optical Genesys TX hard-disabled. One receive epoch only: not a packet/CRC,
remote link-up/discovery, TSC/synchronization or deterministic-latency proof.

Restored Kasli full-checker/23-register Si5324 profile/calibration PASS; Genesys
normal PL/CPU1/CPU0 DHCP192.168.2.3 and TTL/DMA/analyzer/MonInj suite PASS.
Original session statusFAIL preserved: final Ethernet test used obsolete host
NIC default enp1s0. Separate four-board-locked explicit enp2s0 recheck PASS:
20/20 ICMP, exact neighbor MAC,5 TCP connections/1080 exchanges/1129210 bytes.
Wrapper now requires explicit restore network_interface. No extra FPGA reset
or programming needed for recheck. Final baseline restored/validated; locks
released. No flash/SD/OTP or Genesys Si writes; Kasli volatile Si setup/restore
explicit. Four offline acceptance/failure controls PASS.
Evidence evidence/kasli03-external-rx-2026-10-15/acceptance.json plus raw original
FAIL and recheck records. Next safe step: upstream ARTIQ idle return TX and
external AUX echo/status-DOWN service, retaining both-board leases/restoration;
never acknowledge production reset or destination-UP before real RTIO backend.

### 2026-10-15 — physical external Kasli↔Genesys AUX echo hardware PASS

External-only firmware uses unchanged current upstream Rust codec/CRC and
existing qualified AUX PL. It bypasses lab loopback self-test, selects external
RX/PRBS off, enables real ARTIQ idle/AUX TX after readiness and disables UART
request injection. Production ResetRequest remains unsupported; destination
status is DOWN. No simulated ResetAck or destination-UP behavior.

Real KASLI03 master LINK#0 RX became up; master log confirms remote replied
after1 packet. Genesys UART records1 EchoReply and71 DestinationDownReply,
zero SEND_FAIL/RX_ERROR/bad-CRC drops,2 unsupported request drops. The71 DOWN
replies are Genesys-side counts, not independently paired master receipts.
TSC/routing/rank/remote RTIO not implemented by this lab responder; master
initialization text must not be confused with synchronized-satellite success.

Full session PASS under Genesys+three Kasli leases: master RAM startup,
management/local counter-RPC tests, external AUX and restoration. Kasli
full-checker/23-register clock baseline restored PASS. Normal Genesys192.168.2.3
PL/CPU1/CPU0 and physical TTL/DMA/analyzer/MonInj/Ethernet checks PASS. Explicit
enp2s0 avoids previous obsolete-NIC check failure. No flash/SD/OTP or Genesys
Si writes; Kasli volatile Si setup/restore explicit. Leases released.
Six offline acceptance/failure tests PASS; external firmware compile PASS.
Evidence kasli03-external-aux-2026-10-15 and aux-external-firmware-build-2026-10-15.
Next safe stage: real satellite RT packet/SED backend clock/reset/CDC wiring,
then genuine TSC load acknowledgement, routing and remote TTL tests.

### 2026-10-15 — receive-clock real satellite transport RTL PASS

New SatelliteTransport connects existing real RT packet/SED/TTL backend to
AuxEndpoint decoded RT wires on RX clock. Existing whole-packet AuxTxCDC is
reused for16-bit replies crossing to TX, with whole-packet busy rejection and
sticky fatal fault. Actual TSC-load Gray counter crosses to PS; no TSCAck is
emitted by this module. AuxEndpoint exposes existing settled-ready qualifier.
Three simulations PASS11.173s: time load count1, real buffer128→127 replies,
TTL timestamp1450→edge1461, unequal RX8ns/TX11ns/PS13ns, plus unready-RX and
busy/drop negative controls. Testbench overlapping clock rename and held
notification sampling corrected; no passing hardware claim from those failures.
Standalone HDL generation PASS, top/CDC constraints/route/hardware PENDING.
Evidence satellite-transport-simulation-2026-10-15.json. No HW access this stage;
last physical baseline remains restored normal Genesys and Kasli diagnostic.
Next: AuxPS/top integration and actual-load CSR gating of TSC acknowledgement,
then genuine reset/routing and remote TTL; no fake production ResetAck/UP.

### 2026-10-15 — AuxPS/raw20/AXI real satellite integration RTL PASS

Optional AuxPS satellite mode now owns real RTIO/SED transport inside the same
three-domain common-reset group. Appended CSRs expose actual TSC-load count,
RT reply fatal fault, sticky SED flags and spread enable; AUX-only layout stays
unchanged. Six tests PASS: raw20/AXI two-reset-epoch TSC load count, four transport
controls including Kasli fine-width3, and legacy AUX PS regression. Raw20 test
40.125s, transport17.809s, legacy2.297s. Functional reset simulation does not
qualify asynchronous assertion/release timing in silicon. HDL generation PASS.

Kasli uses glbl_fine_ts_width3 (1ns wire machine unit/125MHz coarse clock).
Board integration now matches it; simple TTL remains8ns resolution. Initial
fine0 board build stopped/withdrawn before loading. Corrected top generation
verifies61-bit coarse counter/full_ts<<3,209 generated first-stage CDC bits,
eight Gray constraints and real load/error CSRs. New diagnostic mode
DRTIO_SATELLITE uses JB1/AE13 and JB2/AG14, no extra/unverified pins.

Corrected Vivado build running build-vivado/satellite-fine3-route-2026-10-15;
route/timing/bitstream qualification PENDING. No HW access this stage. TSCAck,
production backend reset/routing/destination-UP are NOT_IMPLEMENTED. Evidence
aux-satellite-integration-2026-10-15.json. Next inspect build constraints/timing,
then gate TSCAck on an actual new TSC-load epoch and validate under both-board
leases/restoration. Do not claim deterministic latency from this laboratory PHY.

### 2026-10-15 — fine3 satellite build and actual-load TSCAck physical PASS

Vivado fine3 satellite implementation PASS: WNS2.560ns/WHS0.007ns,209 retained
first-stage bits/eight passing Gray buses. Bit SHA9bacda697117c222dcc7c74cab0ed0c1447218614fb1e1ce631eb5afc79e3c41.
Build evidence satellite-fine3-top-build-2026-10-15.json supersedes pending route.

External firmware --external --tsc uses unchanged upstream Packet::TSCAck/CRC.
The shared C policy observes actual hardware count0 then increment1, rejects
stale/gapped/faulted observations, preserves consumed count across readiness
loss, and sends no synthetic acknowledgement. Native host compilation executes
the same header's controls; seven host acceptance controls also PASS. Qualified
ELFba905d3ff55ba863b00bc81d4ea071a48e0825b2b1cf110048a81042e6a69ff0.
Older non-final policy build never loaded and marked superseded; wrapper binds
TSC policy hash to current reviewed header before hardware access.

Physical session PASS under Genesys+three Kasli leases: Genesys BASELINE count0,
AUX_TSC ACK count1; native Kasli LINK#0 echo after1 packet and later log proceeds
past TSC without failed-to-sync timeout. Genesys119 DOWN replies,2 unsupported
routing/rank drops, no send/RX errors or TSC REJECT. Real RX-clock TSC loaded
from master RT packet and genuine AUX ACK received. This is only load/ACK
handshake acceptance: physical offset/jitter/repeated-reset deterministic
latency NOT_MEASURED. Routing/rank still timeout; production reset/remote TTL
NOT_VALIDATED. Do not infer destination-UP or full synchronization.

Raw START banner/optical_tx descriptor retain inherited no-RTIO-backend wording;
qualified loaded bitstream actually contains real RTIO/SED, with production
reset/routing/UP absent. Raw evidence remains intact and acceptance.json clarifies.
Normal Kasli diagnostic+23-register clock and Genesys192.168.2.3 dual-CPU local
TTL/DMA/analyzer/MonInj/Ethernet restoration PASS. No flash/SD/OTP/Genesys Si
writes; Kasli volatile clock restore explicit. All leases released.
Evidence kasli03-external-tsc-2026-10-15 and aux-tsc-firmware-build-2026-10-15.
Next safe work: actual SED/PHY reset while preserving TSC, with empty-buffer/
output-state proof, then routing/rank state and remote TTL experiments.

### 2026-10-15 — native-style separate RTIO/PHY reset RTL PASS

SatelliteBackend now inserts reset before domain merging: RTIO queue/input
control reset preserves output PHY state and running TSC; PHY reset is separate,
matching current upstream satman ResetRequest/reset_phy behavior. Registered
applied flags require four backend edges; AuxPS requests/statuses cross clock
domains, default cold holds asserted. SED sticky errors clear on RTIO reset;
RT reply transport faults remain fatal. No firmware ResetAck enabled yet.

11 tests PASS:3 new reset cases (queued outputs cancelled, combined output-zero/
reuse, pending input discarded without phantom capture, queue-only high-output
preservation, continuous TSC),1 raw20/AXI reset-control/two-epoch test,7 existing
SED/input regressions. Buffer124→128 from actual SED. Logs9.179/60.703/14.951s.
Common-reset simulation uses functional model, not silicon reset timing proof.
Initial combined-reset lab build stopped/never loaded after upstream comparison.
Corrected satellite-split-reset-route-2026-10-15 running:213 generated CDC bits/
eight Gray buses; route/timing/bitstream PENDING. No hardware access; prior
normal restored Genesys/Kasli state unchanged. Evidence
satellite-split-reset-simulation-2026-10-15.json. Next qualify build and implement
hardware-confirmed CSR hold/release in real AUX ResetRequest, preserving TSC;
then routing/rank and remote TTL. No production ResetAck/UP claim yet.

### 2026-10-15 — split-reset build qualified; reset firmware host controls PASS

Split-reset Vivado build PASS: WNS2.397ns/WHS0.010ns,213 retained CDC bits,
eight Gray buses; bit500206ab7b931263bc678a32ec74d204c0fb1cb9eca3bdaa8cb5a67f731ff244.
This supersedes previous pending build status. Not loaded on hardware yet.

Optional AUX firmware --external --tsc --reset explicitly confirms/releases both
cold holds before TX enable. ResetRequest then asserts only queue reset, waits
for hardware applied, holds100us, releases and confirms completion, PHY released,
unchanged TSC-load count and no transport/SED fault before encoding ResetAck.
Failure disables TX and halts; destination stays DOWN, routing/rank unsupported.
Nine host tests PASS, including actual C helper with injected MMIO failures;
A53 ELF builds PASS. These do not prove physical TSC continuity or remote reset.
Firmware build evidence aux-split-reset-firmware-build-2026-10-15.json.
No hardware accessed or state changed in this stage. Next extend combined-board
session acceptance/hash binding and run native master reset after external
handshake under all shared leases, restoring both baselines. Remote TTL pending.

### 2026-10-15 — external native Kasli ResetRequest/ResetAck physical PASS

Combined bounded session PASS under Genesys plus all three Kasli locks. Exact
KASLI03 DNA0048458a64b04854, USB001:019; SRAM-only master runtime as previously
qualified. Genesys split-reset bit500206ab and reset firmware0f1ad0c loaded.
Cold PHY/queue release confirmed; external echo and actual TSC load/ACK count1.
Two standard counter/RPC kernels called native core.reset after link setup:
two hardware-confirmed queue resets and two genuine upstream AUX ResetAck
replies. TSC-load count stayed1; master reset-error count0 before and after.
One echo,138 DOWN replies,zero send/RX errors; two routing/rank drops expected.

This proves native reset/ACK interoperation and the observed split reset path,
not measured absolute TSC offset, jitter or deterministic latency. Continuous
TSC and output-state preservation have RTL simulation evidence; count1 alone
is not a physical waveform measurement. Routing/rank and remote TTL remain
NOT_VALIDATED; destination intentionally DOWN.12 host controls PASS, including
missing-ACK/new-master-error rejection. Source/hash guard binds reset firmware.

Kasli full-checker identity/EEM/GTP/SFP and23-register internal125MHz profile
restored PASS (69.645s clock restore). Genesys normal dual-CPU core restored
192.168.2.3; physical TTL/DMA/analyzer/MonInj and Ethernet checks PASS. No
flash/SD/OTP/Genesys Si writes. All leases released. Full raw evidence under
evidence/kasli03-external-reset-2026-10-15. Next implement and test bounded
upstream routing/rank state before advertising readiness or remote TTL.

### 2026-10-15 — real Kasli → DRTIO → Genesys TTL loopback PASS

Implemented fixed direct rank1/destination1 leaf routing/readiness using native
upstream AUX RoutingSetPath/Rank/Ack and DestinationOk packets. Paths store the
local-hop predicate; only destination1 is eligible, after valid path/rank,
actual TSC load, PHY/queue release and no sticky fault. No repeaters/forwarding.
Firmware --external --tsc --reset --dio SHA5b7334559f7db98266c5c593d2843204c0288e1598319e560eac418908fe647c;
reused qualified split-reset bit500206ab.16 host policy/acceptance controls PASS.

Physical full session PASS. Native Kasli log [DEST#1] destination is up. Two
standard artiq_run kernels execute examples/kasli_drtio_dio.py on Kasli, global
channels0x10000/JB1 out and0x10001/JB2 in. Each schedules eight10us pulses at
100us intervals and reads exactly eight rising timestamps through external
DRTIO, all seven spacings100000mu, ninth read empty. Both print
DRTIO_DIO_PASS8 100000. No new master reset/sequence/collision/busy/buffer/TSC
errors. Two preparatory native resets also PASS. Simple PHY physical resolution
8ns; absolute phase,jitter and deterministic link latency NOT_MEASURED.

First attempt reached destination-UP but NAC3 rejected legacy delay syntax
before TTL execution. Corrected core.delay,float pulse duration,parallel-variable
declaration passed static artiq_compile, then final hardware acceptance. Both
raw sessions retained separately. In final raw results legacy remote_drtio
NOT_RUN is generic inherited metadata; acceptance.json clarifies actual DIO
PASS. Reporter corrected for future sessions without rewriting raw evidence.

Kasli diagnostic and internal125MHz clock profile restored PASS; Genesys normal
core192.168.2.3 restored with local TTL/DMA/analyzer/MonInj and Ethernet PASS.
All four shared locks covered load/test/restore and are released. No flash/SD/
OTP/Genesys Si writes. Evidence kasli03-external-dio-final-2026-10-15; instructions
diagnostics/drtio/DIO_EXPERIMENT.md, database examples/device_db_kasli_genesys.py.
Next safe scope: more pulse patterns/error controls and DRTIO stability, then
measured phase/deterministic latency and remaining satellite services.

### 2026-10-16 — external DRTIO varied pulse stability PASS

Two normal Kasli kernels PASS,4096 measured physical JB1/JB2 edges from2048
pulses in256 drained batches. Four width/period pairs800/16000,8000/40000,
10000/100000,30000/250000mu; every high width and rising interval exact.256
empty final reads,eight native core.reset invocations within stability kernels.
No new master RTIO/reset/buffer/TSC or firmware errors.18 host controls PASS;
NAC3 static compilation PASS. Not saturation/maximum throughput qualification.

First session refused JTAG connection before any programming; restoration also
could not connect, so its FAIL record is retained (no board writes occurred).
Old hw_server container absent; another thread's Vivado container occupied its
old172.17.0.2 address. Under shared locks started Genesys-filtered hw_server
34e5dd105b4c at172.17.0.3:3121, leaving other container untouched. This endpoint
supersedes stale address examples until rediscovery. New session passed all
load/test/restoration checks. Kasli diagnostic/125MHz profile and Genesys normal
192.168.2.3 localTTL/DMA/analyzer/MonInj/Ethernet restored PASS. No flash/SD/OTP/
Genesys Si writes. Evidence kasli03-external-stability-v2-2026-10-16. Next genuine
link DOWN/retraining/new-TSC-ACK/UP and repeated DIO, separately from RTIO reset.

### 2026-10-16 — forced GTH reset / external DRTIO recovery PASS

Two bounded Genesys-only monitor_reset assertions1000ms, without PS/PL reload
or Kasli reset. Each native master log gained exactly one LINK#0 DOWN, one link
initialization-completed and destination1 UP. Each new reset epoch emitted one
actual-load AUX_TSC ACK count1; no TSC rejection or new reset/RTIO/buffer/TSC
errors. After each recovery two standard kernels measured8 rising edges at
100000mu spacing. Four post-recovery kernels PASS in total. Separate baseline
DIO and all cycle logs retained, so stale UP or old handshake cannot pass.
19 host tests PASS including missing fresh ACK/transition negative controls.
This is transceiver-reset recovery, not cable-removal or phase/jitter proof.

Kasli full-checker + internal125MHz clock restored PASS. Genesys normal local
core192.168.2.3 restored; TTL/DMA/analyzer/MonInj and ICMP/identity/TCP echo PASS.
All Genesys/all-Kasli locks held across entire session and released. No flash/
SD/OTP/Genesys Si writes. Evidence kasli03-external-recovery-2026-10-16. Next
integrate native distributed-DMA memory reader/CRI ownership and trace protocol;
current satellite image has no DMA engine. Upstream reuse map in DIO_EXPERIMENT.md.

### 2026-10-16 — optional satellite DMA backend offline PASS

Continued existing port: SatelliteBackend optional dma_membus reuses qualified
M-Labs AXI DMA adaptation and upstream CRISwitch. Default DIO backend has no
DMA instance/change to its direct packet path. Native packet->DMA->packet->DMA
quiescent ownership, actual SED/TTL edges, fine3 and nonzero time offset PASS.
Stale trace raises native underflow; error clear and next trace recover without
phantom output. AXI response queues fully drain at completion. Measured519–520
cycles; initial400-cycle test deadline was too short, final bounded deadline1500.

Two DMA tests PASS on Piotr1461cf9 and two on contemporary486e8f8. Existing7 SED
and3 split-reset tests PASS (14 methods across both source variants). Standalone
--dma --fine-ts-width3 HDL generation PASS. No Vivado or hardware access; no PS
CDC/trace protocol claim. Native switch remains firmware-managed; only idle
transaction-free handoffs tested. Active DMA/link/queue reset and simultaneous
packet requests remain unqualified and must be rejected/quiesced before use.

Important integration findings: AXI64-bit/16-beat reader needs128-byte trace
alignment, unlike current satman ALIGNMENT64. Recovered RX can stop; resetting
an AXI reader with outstanding PS reads is unsafe. Next provide running-clock
memory-side isolation/CDC and explicit quiescence, then native AUX trace storage/
status before physical DDMA. Qualified board baselines remain unchanged.
Evidence satellite-dma-offline-2026-10-16; detailed scope/reproducer
 diagnostics/drtio/SATELLITE_DMA.md. No flash/SD/OTP/Si writes or board probes.

### 2026-10-16 — DMA running-clock drain + raw CDC offline PASS

New DMAMemoryGuard reuses existing AXI DMAReader, drains all accepted bursts
on abort independently of blocked consumer, and permits next address epoch
only after completion. No AXI reset/abandoned read on RX loss. New DMARawCDC
uses native AsyncFIFOBuffered with coordinated FIFO reset and read-reset output
for future decoder/CRI. First short-reset test exposed16 phantom zero words;
fixed by seven RX reset edges plus synchronized reset/ready acknowledgements.

9 tests PASS on Piotr and9 contemporary upstream: normal/early abort, delayed
AR/R, SLVERR/restart, stalled FIFO, faster/slower RX, single-sys-edge reset,
and actual RX clock-driver pause in simulator while AXI continues/drains. Resume
contains only new address data; accepted AR and completed RLAST counts match.
Standalone HDL emission PASS. Functional reset model only, not physical timing.
No Gray-bus constraints/PS target/decoder/CRI/AUX DDMA integration yet. Memory
sys must remain clocked/out of reset through done; FIFO reset requires paired
abort for interrupted trace. Qualified hardware images/baselines unchanged;
no board access or persistent writes. Evidence dma-memory-offline-2026-10-16.
Next connect native record decoder and CRIMaster in RX with coordinated abort/
completion/error reporting and queue ownership; then target and AUX trace layer.

### 2026-10-16 — asynchronous native DMA decoder/CRI/SED offline PASS

New AsyncSatelliteDMA composes guarded PS-clock reads, raw async FIFO with EOP,
and upstream RecordSlicer/TimeOffset/CRIMaster in RX. Native terminator triggers
memory drain, explicit final token flushes decoder, stable completion/error
payload crosses back with extra settling before capture. Byte base/time offset
latched at start; alignment and busy starts rejected.64-bit interface enforced.
SatelliteBackend external dma_cri option supplies native CRISwitch; default DIO
path unchanged. No hand-written trace decoder replaces upstream code.

6 engine tests each Piotr/current PASS (4 complete paths+2 admission), extra
width rejection PASS,9 memory and7 SED+3 reset regressions PASS. Actual SED/TTL
fine3 events and offset replay, native underflow timestamp/recovery, AXI error/
recovery, faster/slower clocks qualified in simulation. Abort case first admits
future CRI events, pauses RX driver, drains memory on sys, holds consumer reset
and asserts RX rtio_reset_request into real SED, then resumes with no cancelled
edges and a successful new trace. Cannot undo already-fired output transitions.

Standalone --engine HDL PASS. No physical timing/Gray constraints/CSR/PS target/
AUX trace service or HW access. sys must stay alive through engine.done; external
fault/abort detection required. Trace bounds/record validation/prefetch padding/
watchdog and concurrent ownership policy remain necessary before live use.
Done is admission/drain completion, not elapsed trace duration. Evidence
 dma-async-engine-offline-2026-10-16; SATELLITE_DMA.md updated. Next map hardware
control/status and PS memory interface with checked CDC constraints, then native
AUX trace upload/playback/status. Existing board baselines unchanged.

### 2026-10-16 — bounded DMA PS AXI/CSR peripheral offline PASS

New DMACSR bank4 base0xa0002000: address49,time_offset64,max_bursts32,watchdog32,
start/abort/idle-clear,active/pending/reject and stable error/channel/timestamp/
accepted/completed status. Real AuxPS32-bit AXI bridge/MiSoC bank exercised.
Default immutable arena0x22000000–0x22200000; start rejects alignment/window,
max_bursts<4 or beyond arena,zero watchdog,fault,busy or unacknowledged result.
Multiword fields are MSW-first. Result cannot be overwritten until idle clear.
Fault defaults asserted. Shadow writes do not mutate an accepted trace.

Memory guard now bounds native128-byte reads, reserving3 final request slots
while terminating/draining. Fourteen limit/queue subcases PASS on each source:
limits1,2,3 rejected without AR;4,5,16,32 fit bounds and all RLAST counts equal
accepted AR. Budget fault aborts decoder/SED path and clears only for idle new
epoch. Watchdog requests abort and waits for memory drain, never fakes completion.

4 CSR cases each Piotr/current PASS plus PS busy/clear/shadow case PASS;9 memory
regressions and7 current full-engine regressions PASS.64-bit underflow timestamp
snapshot, pending-result protection, preflight rejection with no reads,
watchdog/restart and missing-terminator budget/restart proved. CSR tests use a
controlled-status CRI target; physical SED/TTL is separate existing qualification.
Standalone peripheral HDL and exact map generated PASS. No board access.

Not yet connected to Genesys PS pins/GT/backend, no physical CDC constraints,
Vivado or hardware claim; AUX DDMA trace allocation/validation still missing.
Read window must include prefetch/drain padding; large valid traces near window
end may exhaust a conservatively bounded allocation. Existing qualified board
baselines unchanged. Evidence dma-csr-offline-2026-10-16. Next connect existing
HP0 read port and target backend/owner/reset, add exact Gray/bundled constraints
and qualify generated/routed artifacts before volatile bring-up.

### 2026-10-16 — optional DMA Genesys target HDL and transport tests PASS

Added --satellite-dma target: checked PS HP0 AXI wiring, DMACSR bank4 at
0xa0002000, always-running sys memory guard and recovered-RX decoder domain.
Native CRISwitch ownership follows synchronized active level after launch;
abort reaches actual SED queue reset while leaving PHY/TSC running. Link/reset/
TSC/error fault conditions gate launch and abort active DMA. Firmware still
must serialize packet traffic and DMA ownership; no concurrent traffic claim.

Two new transport tests each Piotr/current PASS. Native RX-clock command source
proves first TTL edge, cancellation of queued future low transition, preserved
high/TSC and successful later low event/packet-owner return. Incomplete DMA
connections rejected. Initial Python direct one-cycle pulse test lost commands
in aliased simulator clocks; replaced with an RX-register single-command source.
Generated full target HDL/map PASS:383 first-stage bits,10 Gray buses. Physical
DMA constraints pending; generated Vivado script fails closed until added.
No Vivado/HW qualification or board access in this stage. Evidence
satellite-dma-target-offline-2026-10-16. Next exact Gray/bundled constraints,
routed timing checks, then bounded volatile bring-up and AUX DDMA service.

### 2026-10-16 — satellite DDR DMA Vivado/CDC implementation PASS

Optional satellite-DMA target now has exact generated-HDL CDC constraints:
2x5-bit FIFO Gray pointers and64/2/24/64-bit held offset/error/channel/timestamp.
Held sources are explicitly preserved, including constant TTL-target bits.
All164 new data synchronizer endpoints are excluded from the general first-
stage false path, with8ns datapath maximum delay and8ns bus skew. Missing HDL
source/assignment/width fails generation.383 first-stage bits retained exactly.

Vivado2025.2 build-vivado/satellite-dma-route-v3-2026-10-16 PASS, bitstream
3ee1173c22e578f2c4e7d9ec8dc73de258c291ea6e1733d098e7abc135d8396c.
WNS1.416ns/WHS0.003ns,14/14 bus-skew groups PASS (10Gray+4held).
Routed checker independently finds all164 timed endpoints, each with8ns
requirement/nonnegative slack; minimum slack7.157ns. No missing/false-pathed
endpoint can qualify. Final checker binds checkpoint/HDL/map/manifest/TSV by
hash; modified HDL hash negative rejected. Default qualified DIO build still
passes its original8-group checker. Current-upstream HDL generation and twelve
missing-assignment negative cases across legacy/current HDL passed.

Initial attempt hit unsupported collection commands in Vivado Tcl; replaced
with standard concat/foreach/lsearch. A cache path absent in the failed build
was rejected before Vivado; reused original existing shared cache. Negative
false-path test exposed Vivado returning a path with nonnumeric requirement;
checker now explicitly rejects missing/nonnumeric timing before arithmetic.
Build wrapper runs routed checks before accepting a DMA image. Reports/hashes
are under evidence/dma-cdc-implementation-2026-10-16.

No board programming/reset/network/UART access or persistent writes. This is
routed FPGA implementation qualification only: DDR-to-RTIO hardware playback,
AUX DDMA trace upload/validation/allocation/status and concurrent ownership
policy remain unqualified/missing. Normal board baselines untouched. Next
bounded volatile DDR-DMA playback/abort test under all shared device locks,
then native AUX DDMA firmware integration and standard Kasli experiment.

### 2026-10-16 — physical DMA-image cold-release failure reproduced/fixed in RTL

Hardware attempts used routed DMA bit3ee1173c... under all four shared board
leases. First stopped at Kasli netboot TCP timeout; both boards restored PASS.
A separate Kasli-only netboot isolation passed3 TCP connections/MAC identity.
One full retry with unchanged limits passed netboot/runtime/management and
counter kernels, but Genesys AUX firmware failed startup before cold release,
TSC exchange or DIO. No DMA trace/playback ran. Both boards restored PASS:
Kasli full checker+reviewed volatile clock baseline, Genesys normal local
TTL/DMA/analyzer/MonInj/Ethernet192.168.2.3. No flash/SD/OTP/Genesys Si writes.

Root cause: DMACSR forwarded readiness fault to engine.abort even while idle.
No observed TSC is a launch fault; it therefore held the DMA SED reset high.
Firmware waits for RTIO reset release before enabling TX needed to receive
TSC: circular cold-start dependency. Regression using actual AuxPS/SED and
bank4 PS AXI reproduces FAIL before fix. Gate readiness-fault abort by active
DMA epoch; admission still rejects a faulted idle launch with no AXI reads.
Cold-release +5 existing CSR tests PASS each Piotr/current; additional injected
active fault AFTER accepted AR still aborts/drains and next trace recovers on
both sources. Do not reuse old routed DMA bit for further live bring-up.

Firmware builder explicitly excludes the separately owned DMA bank from its
single-word AUX header. Rebuild before adding failure diagnostics produced the
identical qualified5b733455... ELF. Added cold-release failure register dump;
new firmware build PASS with source/map hashes. New Vivado build is RUNNING at
build-vivado/satellite-dma-cold-release-route-2026-10-16 (25min timeout,
build/dma-cold-release-vivado-session-2026-10-16.log). No source/helper edits
until it finishes. Repeat physical cold release/DIO before arming DDR DMA.

Prepared host-armed DMA diagnostic (NOT_RUN): actual PL DMA trace includes
input gate and4 TTL pulses; standard Kasli kernel reads8 physical timestamps.
Synchronous RPC only fills/reads back bounded DDR window and starts CSR engine
under inherited parent lease. It is explicitly not native AUX DDMA. Native
RecordSlicer decodes the exact bytes on both sources; negative timestamp/arena
checks and experiment compilation PASS. Integration into guarded external
wrapper and physical playback remain pending. Abort-to-packet handoff remains
unqualified; do not interpret active-fault controlled-CRI tests as that proof.
Evidence dma-cold-release-offline-2026-10-16 and kasli03-dma-idle[-v2]-hardware-
2026-10-16 / kasli03-netboot-isolation-2026-10-16. Next finish fixed build,
restore cold-release/DIO acceptance, then host-armed DDR-to-RTIO diagnostic.

### 2026-10-16 — corrected DMA image cold release/DIO hardware PASS; read prefetch fixed offline

Cold-release imagee0fd4389788c228808b170f567424728e3b0c6540e7c0929af2e97c18a1c61b1
build PASS: WNS2.486/WHS0.007ns,14bus-skew groups,164timed DMA endpoints,
minimum DMA slack7.319ns. Physical AUX cold release/TSC load, native resets
and two standard Kasli DIO kernels PASS (8 rises each,100000mu spacing).
Both boards restored/checked PASS. Evidence kasli03-dma-cold-release-hardware.

Added opt-in host_dma_session guarded stage: previous successful physical
cold/DIO/restore proof must bind exact bit+firmware. Failed proof negative
rejected offline. Existing all-board parent leases cover host RPC/DAP DDR
access and native Kasli input capture. Native AUX DDMA remains absent.

First DDR attempt failed with generic status; expanded diagnostic captures full
configuration and result before rejecting. Instrumented repeat:2048-byte DDR
readback PASS; address570425344, offset75936927240, max_bursts16,
watchdog134217728 readback PASS; active0,pending1,reject0,error65,channel0,
timestamp0,accepted1,completed1,RTIOreset1,PHYreset0,async-errors0,reply-fault0,
TSC-loads1. No physical DMA pulse acceptance. Both attempts restored normal
Genesys/Kasli and reviewed volatile clock profile PASS. No persistent writes.

A70-request-acceptance AXI model reproduces identical65 on a short trace:
unbounded upstream AR prefetch exhausts cumulative budget before terminator
reaches decoder. Added4 outstanding credits around unchanged reused reader;
accepted RLAST returns credit. Budget/window unchanged; drain/EOP remain native.
Short and exact host-byte trace now complete with no budget error in simulation;
CRI monitor moved to RX to avoid double sampling on faster sys clock. New
regressions check outstanding<=4 throughout. Full final source suites running;
new Vivado build RUNNING at build-vivado/satellite-dma-credit4-route-2026-10-16,
25min timeout/log build/dma-credit4-vivado-session-2026-10-16.log. Do not edit
running build/RTL/qualifier helpers. Next qualify build, repeat physical cold/
DIO for new bit hash, then host-armed physical DDR DMA. Post-abort handoff and
native AUX DDMA upload/allocator/validation/status remain unqualified/missing.

Final prefetch regressions2026-10-16:26 tests each Piotr/current PASS,
including14 read-budget subcases each. Credit4 Vivado remains RUNNING;
no physical DDR-DMA success claimed. Evidence dma-prefetch-offline-2026-10-16.


Credit4 routed implementation completed2026-10-16: PASS, bit SHA256
40dac1f7a5875d015f6df00aefcaa618204ffc86d7f95280d9f636a9d337568c.
All164 DMA CDC endpoints have numeric8ns requirements, minimum slack7.265ns;
artifact-bound routed CDC and top-build checks PASS. Physical cold release,
TSC/reset and two8-rise DIO kernels PASS with this exact bit/firmware;
Kasli checker/volatile clock profile and Genesys normal runtime/TTL/debug/
Ethernet restoration PASS. Evidence kasli03-dma-credit4-idle-hardware-2026-10-16.
Guarded host-armed DDR playback session started only after that proof; its
physical result is separate from this idle qualification.


Physical DDR DMA credit4 session2026-10-16 PASS:2048-byte exact DDR readback,
accepted1/completed1,error0,no rejection/reset/async/reply faults. Standard
Kasli kernel captured4 physical pulses/8 edges, width8000mu, period80000mu,
first_delta1000120mu. Budget16 bursts unchanged. AUX/TSC/native reset and
both DIO kernels also PASS. Both boards and reviewed Kasli volatile clock
profile restored/validated PASS; Genesys normal local TTL/CoreDMA/analyzer/
MonInj/Ethernet PASS at192.168.2.3. No flash/SD/OTP/Genesys Si writes.
Evidence kasli03-ddr-credit4-hardware-2026-10-16/results.json. Host RPC/DAP
uploads and arms; native AUX DDMA remains MISSING, post-abort packet handoff
and absolute phase/jitter/deterministic-link latency remain NOT_QUALIFIED.
Next implement bounded native AUX upload/allocation/validation/playback/status
against upstream packet definitions, with offline negative tests first.


DDMA upload policy2026-10-16 offline PASS: single bounded2048-byte staging
window, source/ID ownership, upstream first/last bits,1536-byte payload limit,
conservative17-byte destination1 TTL records and zero speculative padding.
ASan/UBSan native tests PASS (fragmentation/truncation/bounds/fields/ownership/
busy/max-size/recovery). Not linked into AUX firmware; no HW accessed.
Next upstream-codec DDMA C ABI + packet vectors, then actual upload/cache/
CSR playback/status integration. Physical prior DDR DMA remains host-armed.


DDMA codec ABI2026-10-16: unchanged current upstream packet codec wrapped for
all7 DDMA types, full fields/CRC/padding and pre-parse upload bounds/status.
Host tests PASS including truncation/CRC/max payload and Rust/C layout. A53
build PASS; not loaded. Legacy scalar decoder rejects DDMA explicitly;
service dispatch/store/cache/CSR playback/status integration remains pending.
No HW access. Evidence ddma-codec-offline-2026-10-16; next service integration.


DDMA dispatcher2026-10-16 offline PASS: checked requests -> bounded store ->
reply/status fields, ownership/readiness/time-overflow guards and slot held
through successful status transport. ASan/UBSan host tests use mock admission;
no hardware/backend/cache/CSR integration or physical recovery claimed.
Next firmware checked decode dispatch plus bounded actual backend/status poll.
No HW accessed; normal restored baselines unchanged.


DDMA backend2026-10-16 offline PASS: actual-address DDR/cache/CSR adapter,
MSW-first64-bit config/readback, bounded accepted-counter polling, positive
future-time guards and sticky ambiguous-admission fault. ASan/UBSan mocked IO
PASS; AMD cache/MMIO binding cross-compile A53 PASS;15 CSR offsets match credit4
map. No live dispatch/HW access. Identified missing live TSC snapshot CSR;
TSC-load count cannot establish future deadline. Next implement snapshot/CDC
and tests before enabling AUX playback. Evidence ddma-backend-offline-2026-10-16.


TSC snapshot2026-10-16 RTL/HDL PASS: DMA-only appended request/busy/valid/value
CSRs, coherent64-bit native full_ts transfer through async FIFO, common endpoint
reset invalidates old data.2 asynchronous snapshot tests +2 current DMA transport
regressions PASS; top HDL/map generation PASS. Physical FIFO CDC constraints/
checker not yet extended: build_top refuses new snapshot map before Vivado.
No new bit/firmware/HW access; prior restored credit4 evidence remains valid.
Next exact snapshot FIFO constraints/routed qualification, then bounded firmware
snapshot/time callback and DDMA dispatch. Evidence tsc-snapshot-offline-2026-10-16.


Snapshot CDC2026-10-16 offline PASS: generated HDL exact8 groups/170 endpoints,
including both3-bit snapshot FIFO Gray pointers; all excluded from generic false
paths and constrained8ns maxdelay/skew. Missing endpoint/wrong width negatives
PASS. Routed checker and top checker require8/170 and16 skew groups for this
map, retain old6/164 support. Vivado RUNNING satellite-dma-tsc-route-2026-10-16,
1500s bound, log build/tsc-snapshot-vivado-session-2026-10-16.log. No HW access.
Do not edit running RTL/build/checker helpers. Next inspect implementation and
fix failures if any, then bounded snapshot firmware callback/DDMA dispatch.


Snapshot route2026-10-16 PASS: bit860bb0e5...,8groups/170 individually timed
endpoints,8ns requirement/minslack7.153ns,16skew groups PASS. Bounded firmware
reader added: native snapshot + conservative age allowance, ordered64-bit CSR,
load epoch/readiness guards, timeout100polls/100us. Host ASan/UBSan PASS; CNTPCT/
CNTFRQ age binding A53 compile PASS. No HW accessed/new firmware loaded.
Evidence tsc-reader-offline-2026-10-16 and tsc-snapshot-build-2026-10-16.
Next build snapshot probe firmware, exact-new-bit guarded cold/DIO/snapshot
qualification, then actual AUX DDMA dispatch/status integration.


Physical TSC snapshot2026-10-16 PASS: exact newbit860bb0e5..., snapshot-probe
firmware,4 monotonic fine3 samples; upper-age allowances10000/8066/7800/7800mu.
AUX/TSC/reset +2DIO kernels PASS. All4 shared locks held through both board
restorations PASS; Genesys normal TTL/CoreDMA/analyzer/MonInj/Ethernet PASS at
192.168.2.3. No persistent/Genesys Si writes. Evidence kasli03-tsc-snapshot-
hardware-2026-10-16. Native AUX DDMA still not dispatched; next wire checked
packets to service/backend/live-time/status and test full offline flow first.


Native AUX DDMA wiring2026-10-16 BUILD/OFFLINE PASS, HW NOT_RUN: opt-in --ddma
routes checked packets into store/service, actual DDR/cache/live-time/CSR start,
native reply/status sends and bounded completion poll. Exact immutable maps
required. Host upstream-codec->C-service wire flow PASS with mocked admission;
4 ASan/UBSan policy suites PASS; A53 ELF build PASS. Native service remains
blocked in external_session until dedicated guarded experiment qualification.
No HW accessed. Next standard Kasli distributed-CoreDMA experiment/guarded stage
with exact upload/status evidence and physical8-edge loopback, then restoration.
Evidence native-ddma-offline-2026-10-16. Abort/transportfault fail closed; no
post-error reuse or production/general DDMA claim.


Native DDMA physical attempt2026-10-16: standard CoreDMA example compiles;
exact native-service firmware idle AUX/snapshot/reset/DIO qualification PASS,
both restored. Playback attempt FAIL: Kasli connection closed unexpectedly;
no satellite DDMA packets logged, no physical native-DMA proof. Cause unknown.
Both restorations/normal local TTL/DMA/debug/Ethernet PASS. Added parent UART
finally drain under existing leases before restoring SRAM, to capture master
panic on next bounded diagnostic attempt; fix not yet physically exercised.
Proof-negative tests PASS. Evidence kasli03-native-ddma[-idle]-hardware-2026-10-16.
Next capture master failure and resolve software issue; do not mask failure.


Native DDMA master failure diagnosed2026-10-16: captured UART kernel panic
ptr%64 assertion ksupport442. Actual kernel RV32 callsite expects NAC3 headered
24-byte tuple (address16,flag20), old ksupport returns16-byte C tuple(address8,
flag12). Optional --nac3-dma-abi overlay prepared in isolated Kasli source;
header/zero-init/size assertion mirror proven A53 bridge. RV32 C layout PASS.
Full runtime compile RUNNING build/kasli03-dma-abi-2026-10-16,900s bound/log.
No fixed-runtime HW test; previous attempt failed before satellite DDMA traffic,
both normal baselines restored PASS. Next finish compile and compare ABI headers,
then guarded test of new master runtime. Keep all alignment/error checks.


Native distributed CoreDMA2026-10-16 physical PASS. Corrected Kasli tuple ABI
runtime built with128KiB ROM; first64KiB attempt overflowed; mem.rs/csr.rs/
regions.ld byte-identical to qualified BRAM image. Runtime SHAf0b53c4c... .
Native AUX upload/playback/status(error0)/erase succeeded ID1076235456.
Standard Kasli CoreDMA kernel captured8 physical JB edges: width8000mu,
period80000mu,first_delta1000120mu; no host DAP upload/arming. Snapshot/reset/
2DIO and both restores PASS; normal Genesys TTL/DMA/debug/Ethernet PASS at
192.168.2.3. All4 leases held; no persistent/Genesys Si writes. Evidence
kasli03-native-ddma-fixedabi-hardware-2026-10-16 and kasli03-dma-abi-build-2026-10-16.
Native DDMA PARTIAL: single-slot TTL subset. Next physical repeated playback/
replacement/erase/reupload/fragmentation; abort recovery and general RTIO still
unqualified. Original/reference source checkouts preserved.


Native DDMA lifecycle2026-10-16 physical PASS:3 trace uploads,9 plays (6handle),
72 edges/36pulses. Width/period8000/80000,16000/120000,24000/160000mu;
first_delta1000120mu all9. Replace existing name +erase/reupload +finalerase
PASS, exact AUX upload/3play-status/erase order per phase,9error0 statuses.
All3 reused ID1076235456; measured waveform changes prove updated contents.
Parser negatives PASS. Existing bit/firmware/master runtime unchanged. AUX/
snapshot/reset/2DIO and both restores PASS; local Genesys TTL/DMA/debug/Ethernet
at192.168.2.3. No persistent/Genesys Si writes. Evidence kasli03-native-ddma-
lifecycle-hardware-2026-10-16. Next offline long-trace budget tests then native
fragmentation; abort/phase/general RTIO remain unqualified.


Long native DDMA2026-10-16 offline boundary:4-credit image fails1020-byte trace
with65 before terminator; no physical long upload attempted.2-credit guard now
passes1020-byte/60-record trace,16burst/2048B window unchanged. Payload limit
reduced1536->1024 (whole17B max1020);1530B rejected by store, RTL injected1530B
still proves budget/drain/recovery. Current CSR10+engine/CDC17 PASS; initial
Python recovery-test local variable error fixed/retested. C ASan/UBSan and real
codec1010+10 fragment reconstruction PASS; new A53 firmware build PASS. No HW.
Vivado RUNNING satellite-dma-credit2-route-2026-10-16/1500s; log build/dma-credit2-
vivado-session-2026-10-16.log. Piotr2boundary cases RUNNING. Freeze active build/
RTL helpers. Next route qualification/new exact cold-DIO proof then physical
fragmented29pulse test. Previous short lifecycle hardware baseline unchanged.

Piotr boundary regressions2026-10-16:2/2 PASS (1020B completion,1530B bounded error/drain/restart). Vivado credit2 still RUNNING; no new bit/HW qualification.


Credit2/native fragmented DDMA2026-10-16 physical PASS. Route bit0c8fcc5c...,
8CDCgroups/170endpoints minslack7.228ns,16skew groups PASS. Exact new bit/fw
idle AUX/snapshot/reset/2DIO+restoration PASS, then standard CoreDMA1020B upload
First1010/Last10 crossing record boundary, both upload ACK/playback/error0status/
erase PASS ID1076235456. Physical29pulses/58edges,width8000mu,period16000mu,
first_delta1000120mu; no extraedge/hostDAP. Maximum whole17B trace under1024B
policy, unchanged16burst/2048B window.3 parser/preflight tests PASS. Both
sessions restored normal Kasli/clock and Genesys local TTL/DMA/debug/Ethernet
PASS192.168.2.3; all4locks; no persistent/Genesys Si writes. Evidence ddma-credit2-
build-2026-10-16,kasli03-credit2-idle-hardware-2026-10-16,kasli03-native-ddma-
fragment-hardware-2026-10-16. Next long-handle/replacement and bounded invalid
upload tests; abort/generalRTIO/phase/jitter remain unqualified.


Native long DDMA lifecycle2026-10-16 physical PASS:3 fragmented1020B uploads,
6packets1010/10;9plays (6handle),522edges/261pulses. Width/period4000/16000,
6000/20000,8000/24000mu;first_delta1000120mu all9. Replace/erase/reupload PASS;
18success replies+9error0status in required order.4parser/preflight tests PASS.
New malformed-upload C policy ASan/UBSan PASS:0mockstarts on invalid inputs,
valid recovery2starts; physical malformed traffic NOT_RUN. Both board restores/
normal Genesys TTL/DMA/debug/Ethernet PASS192.168.2.3. All4locks; no persistent/
Genesys Si writes. Firmware/bit unchanged. Evidence kasli03-native-ddma-long-
lifecycle-hardware-2026-10-16,ddma-reject-offline-2026-10-16. Next abort-to-packet
handoff audit/RTL recovery tests; current firmware abort remains fail-closed.


Abort handoff2026-10-16 RTL PASS: reproduced sticky error holdingSED reset;
active-only pulse negative under actual RX clock pause reproduced2 canceled
outputs firing. New held request/RX8-reset-edge ACK/return-to-zero handshake
preserves error telemetry, exposes recovery busy through CSRactive, rejects
starts/clear during recovery. Native packet pulse afterabort withoutsuccessful
newDMA, no cancelededges, AR/RLAST conservation, PHY/TSC preservation PASS.
Final exact-owner tests2 each current/Piotr PASS; current24engine/CDC/CSR/cold
regressions PASS. No HW access/newpolicy. Vivado RUNNING satellite-dma-abort-
handoff-route-2026-10-16/1500s, log build/dma-abort-handoff-vivado-session-
2026-10-16.log. Freeze active RTL/build helpers. Next implementation qualification
then bounded guarded hardware diagnostic; native firmware remains fail-closed
and AUX fault mapping/production recovery still require review.


Abort-handoff implementation2026-10-16 PASS: Vivado routed bit21c187cb...,
8 CDC groups/170 endpoints,8ns requirements, minimum slack7.206ns. No hardware
access. AUX error ABI audit found raw CSR values incompatible with native
master: CRI underflow4/unreachable8 must become AUX1/2. Firmware now maps
0/4/8/12 to0/1/2/3; any internal/unknown error terminates optical service
without sending a status the current master could mistake for success. This
retains fail-closed behavior; does not implement production abort recovery.
Exhaustive256 byte values plus unknownbit256 ASan/UBSan PASS; actual A53/Rust
firmware build PASS ELF668ca20c... . Existing success-only physical results
remain valid; new bit/firmware and physical faults NOT_RUN. Evidence
ddma-status-map-offline-2026-10-16. Next guarded fresh-image idle qualification
and normal native DDMA regression before any bounded physical abort test.
