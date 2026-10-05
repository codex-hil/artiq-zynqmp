#! /usr/bin/env python3

import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Never, Optional, Sequence

from migen.build.generic_platform import IOStandard, Pins
from migen.fhdl.module import Module
from migen.fhdl.structure import ClockDomain, Signal
from migen.genlib.resetsync import AsyncResetSynchronizer
from vivado_integration import XilinxPlatformAuto


class ThisPlatform(XilinxPlatformAuto):
    IO = [
        ("pl_leds", 0, Pins("J14"), IOStandard("LVCMOS33")),
        ("pl_leds", 1, Pins("K14"), IOStandard("LVCMOS33")),
        ("pl_leds", 2, Pins("L13"), IOStandard("LVCMOS33")),
        ("pl_leds", 3, Pins("L14"), IOStandard("LVCMOS33")),
    ]

    def __init__(self, build_dir: Path):
        super().__init__(build_dir)

        self.add_extension(self.IO)

    def create_programmer(self) -> Never:
        raise NotImplementedError()


class Top(Module):
    def __init__(self, platform: ThisPlatform, variant="blinker"):
        super().__init__()

        platform.import_submodules_to(self)
        self.clock_domains.cd_sys = ClockDomain()
        self.comb += self.cd_sys.clk.eq(self.zynq_ultra_ps_e_0.outputs["pl_clk0"])
        self.specials += AsyncResetSynchronizer(
            self.cd_sys, ~self.zynq_ultra_ps_e_0.outputs["pl_resetn0"]
        )

        if variant == "local-rtio":
            from local_rtio import LocalRTIO, connect_ps_hpm0
            # Recovered from Piotr's original Genesys_ZU_revC.xdc, ec8c4a9.
            platform.add_extension([
                ("ttl_out", 0, Pins("AE13"), IOStandard("LVCMOS33")),  # JB1
                ("ttl_in", 0, Pins("AG14"), IOStandard("LVCMOS33")),   # JB2
            ])
            self.submodules.local_rtio = LocalRTIO(
                platform.request("ttl_out"), platform.request("ttl_in")
            )
            connect_ps_hpm0(self, self.zynq_ultra_ps_e_0, self.local_rtio.axi)

        counter = Signal(30)
        self.sync.sys += counter.eq(counter + 1)

        leds = [platform.request("pl_leds", i) for i in range(4)]
        self.comb += [
            leds[0].eq(counter[28]),
            leds[1].eq(counter[26]),
            leds[2].eq(counter[27]),
            leds[3].eq(counter[25]),
        ]


def main(argv: Optional[Sequence[str]] = None) -> None:
    if argv is None:
        argv = sys.argv
    arg_parser = ArgumentParser(prog=argv[0])
    arg_parser.add_argument("-B", "--vivado-build-dir", default=".")
    arg_parser.add_argument("-M", "--migen-build-dir", default="migen-build")
    arg_parser.add_argument("-N", "--no-run", action="store_true")
    arg_parser.add_argument("--variant", choices=["blinker", "local-rtio"], default="blinker")
    p_args = arg_parser.parse_args(argv[1:])

    platform = ThisPlatform(Path(p_args.vivado_build_dir))
    top = Top(platform, p_args.variant)
    platform.build(top, build_dir=Path(p_args.migen_build_dir).absolute(), run=not p_args.no_run)
    if p_args.variant == "local-rtio":
        top.local_rtio.write_map(Path(p_args.migen_build_dir) / "csr-map.json")


if __name__ == "__main__":
    main()
