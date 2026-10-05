# Prototyp ABI kerneli ARTIQ na A53/AArch32

**Wykonanie pod QEMU przeszło. To nie jest działający core device na Genesys.**
Test kompiluje prawdziwy kernel NAC3, ładuje go loaderem M-Labs i wykonuje
na emulowanym Cortex-A53 w EL1/AArch32. Wariant z aktualnym ARTIQ używa
`EnvExperiment`, `Core.reset()` i `TTLOut.pulse_mu()`.

Sprawdzane są: boot EL3/AArch64 → EL1/AArch32/SVC, identyfikator Cortex-A53,
włączone VFP/NEON (wykonuje się również instrukcja NEON), argumenty/zwrot
hard-float, przekazanie i zwrot i64 przekraczającego 32 bity, timeline i
dwa wywołania output oddalone o 50 mu. Wywołania RTIO trafiają do modelu
w pamięci; nie sterują PL. Automatyczny pusty writeback `service=0, tags=:n`
jest sprawdzany, ale nie obsługujemy aplikacyjnego RPC. Wyjątki/unwind
kończą test błędem. Test negatywny zmienia jeden bit argumentu i musi
zakończyć QEMU kodem 3, bez komunikatu PASS.

## Źródła i narzędzia

- NAC3 `322b7bd2537e176d7997f816ae2fb6ab9e029939` (2026-05-12, ostatnia
  baza przed migracją LLVM 19 → 22), bez zmian w kompilatorze.
- Aktualny ARTIQ `486e8f897547d282d46a02c30463449c21e30cfe` i sipyco
  `75f055c2ee29c09a49912e63ed49c7b7cae953c4` w wykonanym teście.
- Loader `artiq-zynq@15c856f315969b5c1d01d2917ed52f1b0f199677`;
  źródła/licencja i opis minimalnych adapterów cache są w `upstream-dyld`.
- Rust 1.99.0 do kompilatora, Rust 1.87.0 do runtime, LLVM 19.1.1,
  GCC ARM 13.3 i QEMU 8.2.2. Dokładne Ubuntu packages i SHA-256:
  `scripts/abi-tools.json`. Narzędzia są lokalnie wyciągnięte z `.deb`,
  bez sudo i bez zmiany systemowych pakietów.

Obecny HEAD NAC3 wymaga LLVM 23. Nie został cofnięty ani zmodyfikowany;
prototyp ma osobny checkout. Jego pozytywny wynik nie oznacza przetestowania
HEAD NAC3 ani wszystkich typów, instrukcji i funkcji języka ARTIQ.

## Odtworzenie

Wymagane: Ubuntu 24.04, Python 3.12 z pip, git, Rust/rustup, apt i dpkg-deb.
Wszystkie duże katalogi kieruj na wolumen danych. Utwórz venv tak jak w
głównym README, a potem:

```sh
python -m pip install -r requirements-kernel-abi.txt
git clone https://git.m-labs.hk/M-Labs/nac3.git /large-disk/nac3-abi
git -C /large-disk/nac3-abi checkout 322b7bd2537e176d7997f816ae2fb6ab9e029939
python scripts/setup_abi_tools.py --output /large-disk/abi-tools
rustup toolchain install 1.87.0 --profile minimal
rustup target add --toolchain 1.87.0 armv7-unknown-linux-gnueabihf
```

Kompilator budowany jest przez `cargo +stable`; wykonany build używał
1.99.0. Runtime zawsze używa `+1.87.0`. Jeśli rustup jest w innym miejscu,
runner przyjmuje osobno `--compiler-rustup-home` i `--runtime-rustup-home`.
W razie usunięcia przypiętego pakietu z serwera Ubuntu skopiuj zabezpieczone
pliki `.deb` do `abi-tools/debs`; setup nadal sprawdzi wszystkie SHA-256.

Minimalny test z fixture NAC3:

```sh
make test-kernel-abi PYTHON=/path/to/venv/bin/python \
  NAC3_SOURCE=/large-disk/nac3-abi ABI_TOOLS=/large-disk/abi-tools \
  O=/large-disk/build
```

Test z prawdziwymi klasami ARTIQ wymaga aktualnych checkoutów ARTIQ i sipyco:

```sh
make test-kernel-abi PYTHON=/path/to/venv/bin/python \
  NAC3_SOURCE=/large-disk/nac3-abi ABI_TOOLS=/large-disk/abi-tools \
  ABI_ARTIQ_SOURCE=/path/to/artiq ABI_SIPYCO_SOURCE=/path/to/sipyco \
  O=/large-disk/build
```

`results.json` zawiera status EMULATED, revisions, wersje, hashe artefaktów
i polecenia. Każdy krok zapisuje log, a nieudany krok pozostawia INCOMPLETE.
Nie wymaga Vivado, Vitis, Linuxa w guest ani fizycznej płyty.

## Ograniczenia i decyzja

Bare-metal image linkuje wyłącznie `core`/`alloc` z targetu Rust
`armv7-unknown-linux-gnueabihf`, bez `std`/libc/Linux runtime. Jest to
pragmatyczny sposób uzyskania A-profile hard-float na stable do tego testu;
produkcyjny target, startup i polityka MMU/cache wymagają osobnej integracji.
Nie używamy bibliotek `armv7r` dla A53: linker wykazał konflikt profili R/A.

QEMU `virt` ma własne adresy RAM i PL011. Firmware startuje na CPU0,
z wyłączonymi cache i MMU; warunek ten jest sprawdzany. Nie wolno używać
tych adresów ani adaptera cache jako firmware Genesys. Loader przyjmuje
wyłącznie zaufane lokalne artefakty, a proces userspace używa RWX jako
ograniczenia prototypu. Nie ma testów scheduler/RPC, unwindingu, IRQ,
DMA, izolacji kernela ani niezawodności wielokrotnego ładowania.

Wynik uzasadnia kontynuowanie integracji A53/AArch32 z istniejącym
backendem Cortex-A9. AArch64 warstwa boot/diagnostyki może pozostać osobno;
nie można bezpośrednio wywołać ELF32 funkcją z AArch64. Kolejne kroki:
produkcyjny target Rust A-profile, obsługa wyjątków/unwind, RTIO CSR adapter,
następnie management, transport kernela i prawdziwe RPC. Finalną decyzję
potwierdzi uruchomienie tej ścieżki przez istniejący FSBL na Genesys.
