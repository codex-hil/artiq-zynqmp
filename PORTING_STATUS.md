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
| build | PARTIAL: Rust, Vivado, Vitis, Yocto | Nix/nightly 2023; własny target JSON | Cargo stable, Migen/Vivado, AMD CMake/SDT | PARTIAL: R5/A53, oba bitstreamy, PMU/FSBL PASS; runtime ARTIQ MISSING | `make test hdl`; logi w evidence |
| PS | Własne TCL, eksport pinów/XCI | ZCU111 HAL i SLCR | AMD PS IP; LiteX ZynqMP | PARTIAL: zachowano TCL Piotra; wariant HPM0/125 MHz | Vivado 2025.2 blinker/local RTIO PASS; JTAG/PS/CSR hardware PASS |
| AArch64 | main: biblioteka C ABI; startup delegowany BSP | Własny startup, wyjątki, multicore | AdaCore 0.2.0, aarch64-cpu | PARTIAL: fizyczny A53/EL1 OCM PASS; DDR startup/MMU diagnostyki PASS | JTAG + UART evidence; autonomiczny boot NOT_RUN |
| R5/OpenAMP | wip: BSP C i przykład echo; Rust pusty loop | Brak równoważnej ścieżki | AMD/OpenAMP/libmetal | PARTIAL: oryginalna biblioteka kompiluje; brak wykonania kernelów | Cargo R5; OpenAMP hardware NOT_RUN |
| DDR | Dynamiczne SPD/FSBL, lokalne xfsbl_ddr_init.c | Własny SPD/PHY dla ZCU111 | AMD FSBL + Digilent BSP | PARTIAL: FSBL Piotra + AMD 2025.2 uruchomiony; DDR test 128 KiB PASS | evidence/a53-ddr-hardware-2026-10-07.json; pełny zakres/stress NOT_RUN |
| UART | MIO18–19 / 115200, BSP C | UART + generator baud | AdaCore UART/embedded-io | DONE UART diagnostic: TX i PING/PONG fizycznie PASS | `evidence/a53-ocm-hardware-2026-10-07.json` |
| GIC | R5 helper używa XScuGic/IPI | Własny GIC400 | arm-gic 0.6.1 | DONE diagnostic PPI30: fizycznie PASS, poprawiony widok EL1 NS | `evidence/a53-ocm-hardware-2026-10-07.json` |
| timer | PS TTC0 skonfigurowany; brak testu ARTIQ | Global timer/time/async delay | Generic A53 timer | PARTIAL: polling i PPI30 fizycznie PASS | Częstotliwość fizyczna niezmierzona; evidence OCM |
| clocks | TCL i FSBL PS PLL; LED counter | Własna inicjalizacja SLCR PLL | AMD; LiteX config/preset | PARTIAL: local-rtio żąda PL0 125 MHz | Estymacja counter/monotonic w teście sprzętowym; NOT_RUN |
| Ethernet | ENET0 MIO26–37, MDIO76–77; Linux | GEM/PHY/smoltcp; uwagi o ograniczeniach TX | AMD GEM, Linux macb; Zynq7000 NAR3 | PARTIAL: GEM0 bare-metal DHCP/ping/TCP echo fizycznie PASS; Rust management transport PASS; kernel/RPC MISSING | MDIO/link/DHCP/20 ping/1,129,210 B TCP PASS; RPC NOT_RUN |
| AXI | Historyczny read-only slave 0x80000000; usunięty z późniejszego kodu | AFI HP/HPC rejestry, bez ARTIQ | LiteX AXI2Wishbone; MiSoC CSR | PARTIAL: HPM0_FPD -> CSR 0xA0000000; naprawiony importer PS | Symulacja AXI/ID/backpressure/CSR PASS; fizyczny CSR readback przez PS DAP PASS; A53 MMIO counter via TCP PASS |
| RTIO | MISSING: tylko migacz LED | MISSING integracja ARTIQ | ARTIQ TSC/Core/SED/KernelInitiator | PARTIAL: prawdziwy upstream RTIO, 2 kanały, coarse 8 ns przy 125 MHz | Counter i wewnętrzny scheduled TTL probe hardware PASS; fizyczny loopback NOT_RUN |
| TTL output | MISSING | MISSING | ttl_simple.Output | PARTIAL: JB1/AE13, LVCMOS33 z XDC Piotra | Odstęp zboczy 50 taktów w symulacji; fizyczny determinism NOT_RUN |
| TTL input | MISSING | MISSING | ttl_simple.Input | PARTIAL: JB2/AG14, synchronizacja i timestamp FIFO | Symulowany loopback PASS; fizyczny loopback NOT_RUN |
| DMA | MISSING | PS/SD/GEM DMA ≠ RTIO DMA | ARTIQ RTIO DMA; zynq DMA adapter | MISSING: brak transportu DDR->CRI ZynqMP | NOT_RUN; suite nie zgłasza sukcesu DMA |
| analyzer | STUB serwera TCP1382 | Brak integracji | ARTIQ analyzer + NAR3 protokół | MISSING sprzętowy recorder/DDR i obsługa sieci | NOT_RUN |
| moninj | STUB serwera TCP1383 | Brak integracji | ARTIQ MonInj | PARTIAL: CSR probes/injection; TCP nadal STUB | Fizyczny CSR output probe PASS; pełny protocol NOT_RUN |
| management | STUB: handler `pass`, TCP1380 | Nie zastępuje NAR3 mgmt | artiq-zynq management | PARTIAL: Rust A53 + AMD/lwIP TCP1380; GetLog/ClearLog/read-only metadata | Aktualny artiq_coremgmt log/config oraz 9 testów hardware PASS |
| RPC/kernel | STUB: LoadCompleted/KernelFinished bez wykonania ELF | Board runtime, nie runtime ARTIQ | NAR3 loader/ksupport/RPC/unwind | PARTIAL prototypu ABI: rzeczywisty kernel NAC3 na emulowanym A53/AArch32; MISSING runtime/RPC produkcyjne; stub zwraca błędy | 6 testów framing/rejection; ABI QEMU PASS z aktualnym ARTIQ i negatywną kontrolą |
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
