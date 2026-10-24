"""Pinned local source dependencies, never modify dependency checkouts."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
for path in [
 '/home/codex-hil/kasli-diot-switch/reference/migen',
 '/home/codex-hil/ccd-hdl-review/reference/litex',
 '/home/codex-hil/trenz-bringup/reference/liteiclink',
 '/home/codex-hil/trenz-bringup/reference/litejesd204b',
 '/home/codex-hil/fit-bringup/sources/liteeth-eth-check',
 '/home/codex-hil/open-miqro-awg/upstream/misoc',
 str(ROOT/'vendor/phaser')]:
 sys.path.insert(0,path)
