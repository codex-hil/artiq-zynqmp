# Odtwarzanie buildów i problemy zgodności

Nie uzyskano jeszcze wszystkich oryginalnych artefaktów Piotra. Zweryfikowano
obie biblioteki Rust, generację HDL i współczesne rozszerzenia diagnostyczne.
Nowe XSA, bitstream, FSBL/app oraz boot.bin wymagają dalszego buildu FPGA/BSP.

| Problem / obserwacja | Rozwiązanie / wynik |
|---|---|
| main i wip mają różne architektury/build systems | Zabezpieczono oba refs; rozwój jest na osobnej gałęzi wyprowadzonej z wip |
| GitHub ARTIQ/Migen/MiSoC przestał odpowiadać aktualnemu upstream | Pobranie canonical M-Labs do osobnych refs/mirrorów; zachowanie snapshotów GitHub |
| Relative URL elhep/migen po lokalnym clone | Lokalny URL submodule ustawiony w git config; przypięty SHA pozostaje oryginalny |
| Git domyślnie blokuje file transport dla submodules | `git -c protocol.file.allow=always submodule update` wyłącznie dla własnych mirrorów |
| Root filesystem miał mniej niż1 GB wolnego miejsca | Wszystkie duże sources/work/build/toolchain/cache przeniesiono na `/srv/codex-hil-data/artiq-zynqmp` |
| Checkout BSP przerwany przez brak miejsca | Po przeniesieniu przywrócono dokładny oryginalny gitlink; bez zmiany kodu upstream |
| Brak systemowego ensurepip/python3-venv | Użyto izolowanego venv na dużym wolumenie i oficjalnego bootstrap pip; nie zmieniono systemowego Python |
| Brak Migen/colorama/numpy/sipyco/MiSoC | Izolowane Python deps, pinned revisions; `requirements-host.txt` i log pakietów |
| envsetup wymagał obecności obu settings64.sh | Source tylko istniejących backendów; można budować Rust/HDL/testy bez Vivado/Vitis |
| WIP Makefile nie śledził Cargo.toml/lock/config | Dodano prerequisites i cargo `--locked` |
| Rust targets nie były zainstalowane | Dodano AArch64 i R5; toolchains1.75 i1.87 w osobnym taskowym RUSTUP_HOME |
| Nix miał tylko target R5 | Dodano AArch64 do istniejącego Rust1.87; zgodny rust-toolchain.toml poza Nix |
| Nix submodules fetch wpadał na brak gen-machine-conf | Recursive submodule update; zabezpieczono nested pin; metadata przechodzi |
| Nix store/cache na pełnym root filesystem | Metadata sprawdzono z osobnym local store/cache na dużym wolumenie; nie zmieniono globalnego Nix store |
| Brak `vivado` | Próba oryginalnego 0_platform kończy się127; brak nowego XSA/bitstreamu. Nie udawano wykonania Vivado |
| WIP 3_bootable używa Vitis Python API | Pozostawiono golden workflow; nowy A53 diagnostic buduje Cargo/LLVM bez Vitis. Pełny vendor C BSP build bez Vitis jeszcze nie odtworzony |
| Importer PS kierował wejścia w złą stronę | Testy wykazały 4 FAIL na oryginale; poprawiono wejścia/offsety; 5 PASS |
| PL reset release nie był synchronizowany | Dodano AsyncResetSynchronizer z zachowaniem PS resetn0 |
| Piotr daemon zgłaszał sukces ELF bez wykonania | LoadFailed/KernelStartupFailed, limit rozmiaru, sprawdzenie truncation i zamknięcie socketów |
| Pojedynczy kanał RTIO powoduje Memory(depth=1) assertion upstream | W realnym wariancie są2 wymagane kanały output/input; nie patchowano arbitralnie RTIO |
| Rzeczywisty PS MAXIGP ma40-bitowy address bus | Potwierdzono w HWH Piotra; zachowano40 bitów w AXI i Wishbone zamiast założyć32 |
| MiSoC Wishbone nie ma LiteX `addressing` metadata | Użyto LiteX Wishbone interface dla mostu, MiSoC WB2CSR dla ABI |
| Stała pipeline latency RTIO była pominięta w pierwszej asercji | Test sprawdza deterministyczny odstęp50 taktów, a nie wymyśloną latencję PHY; loopback sprawdza timestamp |
| AdaCore link script nie narzuca ELF entry | Dodano ENTRY(__start); wcześniejszy ELF miał entry0, poprawny ma entry w kodzie |
| Cargo nie reagował na memory.x | Build script kopiuje script do OUT_DIR i używa rerun-if-changed |
| DDR test bez maintenance mógłby czytać sam cache | Buffer wyrównany64 B; dc cvac + dsb + dc ivac + dsb/isb przed readback |
| Brak known Genesys UART/JTAG endpoint | Nie otwierano cudzych lokalnych urządzeń; hardware suite zapisuje NOT_RUN |

## Granice weryfikacji

Nix metadata nie jest równoważne działającemu `nix develop` ani pełnemu
buildowi kompilatora ARTIQ. Użyty host build nie wymaga compiler frontend:
importuje rzeczywiste gateware i wykonuje symulację Migen.

GIC/timer/UART/DDR diagnostics zostały zbudowane, nie uruchomione. Dynamiczne
DDR Piotra/AMD musi zakończyć się sukcesem przed skokiem do A53 ELF w DDR.
Test128 KiB nie jest testem całej pojemności DDR ani długiej stabilności.

Wszystkie niepowodzenia i granice artefaktów są zachowane zamiast zamieniane
na puste pliki platform.xsa/top.bit/boot.bin. Stary bitstream w XSA Piotra
pozostaje historycznym artifactem, a nie rezultatem nowego buildu.
