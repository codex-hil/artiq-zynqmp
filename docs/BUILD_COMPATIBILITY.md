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

## Prototyp kernel ABI

- Aktualny NAC3 wymaga LLVM 23; wybrano osobny pin z maja 2026 z LLVM 19,
  pozostawiając HEAD bez edycji. Build z systemowo wyciągniętym LLVM 19 przeszedł.
- Rust armv7r core/alloc nie można linkować do A-profile: rzeczywisty linker
  odrzucił profile R/A. Test bare-metal korzysta z armv7-unknown-linux-gnueabihf
  core/alloc i nostdlib, bez Linux runtime. Produkcyjny target pozostaje do integracji.
- Relokacyjny loader M-Labs używa privileged Cortex-A9 cache operations;
  adapter testowy rozdziela userspace cacheflush i bare-metal z wyłączonymi cache.
- QEMU virt umieszcza DTB przy 0x40000000: bootstrap przeniesiono na 0x40100000,
  payload ARM32 na 0x40200000. Adresy te nie są adresami Genesys.
- Nowy ARTIQ wymaga aktualnego sipyco get_exc_message; użyto osobnego checkoutu
  sipyco-canonical, bez wymiany zależności istniejącego projektu.
- Nawet pusty kernel emituje automatyczny rpc_send_async writeback. Test
  sprawdza service=0 i tag :n; pozostałe RPC i unwind jawnie kończą go błędem.

## Network kernel integration (2026-10-07)

The offline embedded ABI probe did not require application RPC return
allocation. Real Core.run/RPC emitted an undefined `malloc` reference, and
CPU1 correctly returned LoadFailed. Added malloc/free bindings backed by
linked_list_allocator 0.10.5, with separate runtime/kernel heaps and reset on
new upload. Real artiq_run now passes i64/float/counter RPC and return tests.

Current upstream embedded-io 0.7.1 requires core::error::Error in addition to
kind(); the bounded writer supplies Display/Error. Formatting loader errors
pulled alloc's _Unwind_Resume into the ARM staticlib; unsupported unwinding
is explicitly routed to worker failure, not silently swallowed.

Old run_ethernet.tcl halted every A53, which would stop the new CPU1 worker.
Added run_a53_runtime.tcl preserving CPU1; boot runner starts worker before
CPU0 and checks its READY mailbox event. Added separate cacheline producers
and AMD CPU0 cache flush/invalidate; CPU1 remains cache/MMU-off for this
bring-up. Management counter reads are guarded while CPU1 uses the shared
hardware latch. See boards/genesys_zu-5ev/3_kernel/README.md for limits.

## Local RTIO kernel bindings — 2026-10-07

The 512-bit o_data CSR is 16 big-order 32-bit words, not a single u32:
writing its LSW at base+60 triggers the event. Generated word counts now
accompany addresses. 64-bit now/i_timeout/counter/timestamps use MSW first.
Kernel timeline was software-only; it now uses rtio_now in PL. Output WAIT
is backpressure (poll, never duplicate-submit); underflow/overflow are
explicit fail-stop until exception/unwind integration. Finished reads actual
async_error and W1C-clears it, instead of the old no-output constant zero.
Fresh CPU0 and CPU1 builds passed; CPU0 UART banners no longer incorrectly
claim kernels/RTIO exports are unavailable for every worker image.
Direct unittest initially lacked ARTIQ on PYTHONPATH; rerun with the pinned
reference/artiq passed actual AXI/RTIO scheduled TTL simulation.

## Native ARM exception integration — 2026-10-08

Preserved M-Labs EHABI/LLVM sources build with Clang19, Cortex-A9 hard-float.
Removed -flto from the imported unwinder build: GNU final ld cannot consume
LLVM bitcode. C/Rust force unwind tables; linker exposes bounded exidx/extab.
Freestanding newlib headers needed _FORTIFY_SOURCE=0 for GCC compilation;
otherwise stdio requested absent ssp/stdio.h. Existing Rust libunwind abort
symbol replaces temporary C abort to avoid a duplicate definition.

Uncaught exception packet initially optimized Vec<u8> appends into unaligned
word stores under CPU1 MMU-off; actual A53 data abort pinpointed the store
in core1::terminate. Switched to volatile byte stores in the existing mailbox,
matching the working RPC writer. Explicit worker_invoke boundary prevents
unwinding into the polling activation. Import origin/license/hash manifest
and minimal adaptations recorded in worker ORIGIN.md/EXCEPTION_SOURCES.json.
