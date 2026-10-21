# Przekazanie Vivado na serwer Dell

Stan na 2026-10-21. Odbiorcy: wątki budujące projekty FPGA na Optiplexie.
Nowe ciężkie buildy Vivado należy uruchamiać na Dellu `192.168.2.7`.
Optiplex pozostaje stacją debug z dotychczasowymi połączeniami sprzętowymi.
Istniejące buildy, lokalne launchery i serwer JTAG nie zostały przełączone.
Zgodnie z ostatnią decyzją użytkownika **nie usuwać instalacji ani instalatorów
z Optiplexa**.

## Dostęp i środowisko

| Element | Wartość |
|---|---|
| SSH | `codex-hil@192.168.2.7` |
| Klucz na Optiplexie | `/home/codex-hil/.ssh/dell_build` |
| Vivado | 2025.2, launcher `/home/codex-hil/.local/bin/vivado` |
| Bootgen | `/home/codex-hil/.local/bin/bootgen` |
| Powłoka narzędziowa | `/home/codex-hil/.local/bin/vivado-container shell` |
| Instalacja na NVMe nr 2 | `/srv/nvme-fast-2/toolchains/amd/Xilinx` |
| Zachowana ścieżka instalacji | `/srv/codex-hil-data/toolchains/amd/Xilinx` (przez symlink) |
| Szybkie katalogi | `/srv/nvme-fast-1` do `/srv/nvme-fast-4` |
| Domyślne buildy | `/srv/nvme-fast-1/vivado-work` |
| TMPDIR kontenera | `/srv/nvme-fast-1/vivado-tmp` |
| Host | Ubuntu 26.04.1, i7-9800X, 8 rdzeni / 16 wątków, 64 GB RAM |
| Kontener | Ubuntu 22.04.5, rootless Podman |

Instalację i dane narzędzi przeniesiono z SATA na NVMe nr 2.
Buildy i TMPDIR pozostają na NVMe nr 1. Nie zmieniać istniejących skryptów
z powodu przeniesienia: stara ścieżka jest zachowana przez dowiązanie.
SATA systemowy służy systemowi; dodatkowy SATA 240 GB pozostaje miejscem
na lokalne kopie, niezależnym od backupu offline.

Nie kopiować klucza prywatnego na Della. Hasło nie jest potrzebne do tego
połączenia. Nowa stacja debug wymaga własnego klucza i autoryzacji.
Adres jest obecnie używanym IP; rezerwacja DHCP nie została ustawiona.

W nieinteraktywnym SSH PATH może pomijać `.local/bin`, dlatego używać pełnych
ścieżek. Szybki test z Optiplexa:

```bash
ssh -i /home/codex-hil/.ssh/dell_build -o BatchMode=yes codex-hil@192.168.2.7 \
  '/home/codex-hil/.local/bin/vivado -version'
```

## Wysyłanie projektu

Każdy wątek używa osobnego katalogu projektu i nowego katalogu dla każdej próby.
Nie synchronizować plików do katalogu z działającym buildem. Poniższy przykład
uruchomić na Optiplexie w Bash; zmienić `source_dir` i `project`.

```bash
set -euo pipefail
source_dir=/home/codex-hil/MOJ_PROJEKT
project=moj-projekt
[[ "$project" =~ ^[a-zA-Z0-9_-]+$ ]]
job="${project}-$(date -u +%Y%m%dT%H%M%SZ)-$$"
remote_dir="/srv/nvme-fast-1/vivado-work/$job"
ssh_key=/home/codex-hil/.ssh/dell_build
remote_host=codex-hil@192.168.2.7

ssh -i "$ssh_key" "$remote_host" "mkdir -p '$remote_dir'"
rsync -a --exclude=.git --exclude=.venv --exclude=.Xil \
  -e "ssh -i $ssh_key" "$source_dir/" "$remote_host:$remote_dir/"
printf 'Build directory: %s\n' "$remote_dir"
```

Przed wysłaniem przejrzeć zakres: katalog projektu nie powinien zawierać
sekretów ani niepotrzebnych wielkich artefaktów. Nie używać `--delete`.
Zachować lokalny zapis commitu, statusu Git, różnic oraz sum plików wejściowych;
samo SHA commitu nie opisuje niecommitowanych zmian.

`rsync -a` zachowuje symlinki. Zależności spoza projektu i absolutne symlinki
trzeba jawnie odtworzyć na Dellu. Pliki `.git` worktree i stare `.venv` nie są
przenośnym środowiskiem. Projekty zależne od Git podczas generowania wymagają
poprawnego checkoutu na Dellu zamiast tego przykładowego kopiowania bez `.git`.

## Uruchomienie i odebranie wyniku

Najpierw ustalić właściwy skrypt Tcl i jego argumenty z instrukcji projektu.
Przykład zakłada `build.tcl` w katalogu głównym. Uruchomić w tej samej powłoce
co wysyłanie, aby zachować `remote_dir`, `ssh_key`, `remote_host` i `job`.

```bash
ssh -i "$ssh_key" "$remote_host" \
  "cd '$remote_dir' && flock /srv/nvme-fast-1/vivado-work/.vivado-build.lock /home/codex-hil/.local/bin/vivado -mode batch -nojournal -log vivado.log -source build.tcl"
```

Wspólna blokada `flock` szereguje buildy używające tego polecenia. Nie blokuje
wywołań omijających ją; wszystkie wątki powinny stosować tę samą ścieżkę.
Na początek uruchamiać jeden ciężki build naraz. W Tcl można ustawić
`set_param general.maxThreads 8`; nie wszystkie etapy Vivado wykorzystają osiem
wątków. Śledzić RAM i wolne miejsce: każdy NVMe ma około 234 GiB, osobno.

Polecenie powyżej działa na pierwszym planie; zerwanie SSH nie jest bezpieczną
metodą pozostawienia zadania w tle. Dla pracy bez aktywnego połączenia przygotować
osobny skrypt i usługę użytkownika lub sesję terminalową z zapisanym kodem wyjścia.
Nie uznawać istnienia starego `.bit` za dowód udanego nowego buildu.

Po zakończeniu odebrać artefakty i raporty, dostosowując `build/` do projektu:

```bash
mkdir -p "$source_dir/remote-results/$job"
rsync -a -e "ssh -i $ssh_key" \
  "$remote_host:$remote_dir/build/" "$source_dir/remote-results/$job/"
scp -i "$ssh_key" "$remote_host:$remote_dir/vivado.log" \
  "$source_dir/remote-results/$job/vivado.log"
```

Sprawdzić kod zakończenia, błędy w logu, timing, DRC oraz SHA-256 artefaktów.
Pliki `.bit`, `.bin`, `.xsa`, checkpointy i raporty pobierać zgodnie z potrzebami
projektu. Wyniku testu kompilacji nie przedstawiać jako testu fizycznej płytki.

## Granice migracji i sprzęt

- Skopiowana została instalacja narzędzi, nie wszystkie projekty, Python venv,
  Nix, Migen/LiteX/ARTIQ ani dodatkowe kompilatory. Generowanie HDL i firmware
  może wymagać osobnego odtworzenia zależności lub wykonania go na Optiplexie.
- Launcher montuje instalację tylko do odczytu, `/home/codex-hil` i cztery NVMe
  do zapisu. Nie montuje dowolnych innych ścieżek pod `/srv/codex-hil-data`.
- Kontener nie ma sieci ani USB. Nie skonfigurowano licencji sieciowych.
  Wynik syntezy Zynq-7020 nie potwierdza licencji dla Zynq-7045; na Optiplexie
  ten większy układ wcześniej wymagał brakującej licencji Enterprise.
- W powłoce kontenera UID 0 jest mapowany na zwykłego użytkownika hosta;
  nie jest to kontener z uprawnieniami root hosta.
- Programowanie JTAG, reset, UART i testy urządzeń pozostają na Optiplexie.
  Obowiązują instrukcje projektu i jego istniejące blokady sprzętu, w tym
  `/home/codex-hil/.cache/genesys-210383B7F02DA.lock` dla Genesysa.
- Nie uruchamiać z Della skryptów sprzętowych ani nie kopiować lokalnych plików
  blokad jako zamiennika koordynacji. Blokada kompilacji jest niezależna od
  blokady dostępu do płytki.
- Przed uruchomieniem przeczytać projektowe AGENTS.md i najnowszy stan sprzętu.
  Nie zatrzymywać istniejących kontenerów ani hw_server na Optiplexie.

## Wyniki przekazania

Instalacja: 62 512 461 247 bajtów, 472 234 zwykłe pliki.
Porównanie `rsync -aHnci` po transferze: PASS, brak różnic.

| Test na Dellu | Wynik |
|---|---|
| Vivado 2025.2, Bootgen 2025.2 | PASS |
| Synteza `xczu5ev-sfvc784-1-e` | PASS |
| Synteza `xc7a100tfgg484-3` | PASS |
| Synteza `xc7k160tffg676-3` | PASS |
| Synteza `xc7s15ftgb196-1` | PASS |
| Synteza `xc7z020clg400-1` | PASS |
| Spartan-7 placement, routing, bitstream | PASS |
| Spartan-7 setup / hold slack | 7.343 ns / 0.252 ns |
| DRC podczas generowania bitstreamu | 0 błędów |
| Programowanie sprzętu podczas migracji | Nie wykonywano |

Dowody na Optiplexie: `/home/codex-hil/artifacts/dell-vivado-migration/status.json`
oraz sąsiedni katalog `validation/`. Na Dellu:
`/srv/codex-hil-data/toolchains/amd/shared/state.json` i
`/srv/nvme-fast-1/vivado-work/migration-validation`.

Obraz runtime i Dockerfile są na Dellu w
`/srv/codex-hil-data/toolchains/amd/shared/container/`.
To zwalidowana kopia instalacji, nie próba instalacji od zera z pakietu AMD.
Pełne odtworzenie awaryjne ze skryptów i backupów pozostaje osobnym zadaniem.
