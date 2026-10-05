#! /bin/false --

from pathlib import Path
from string import digits
from typing import Dict, Iterator, Never

from migen.build.xilinx.platform import XilinxPlatform
from migen.fhdl.module import Module
from migen.fhdl.specials import Instance
from migen.fhdl.structure import Signal

MI_PART_TXT = "mi_part.txt"
MI_BD_CELLS_TXT = "mi_bd_cells.txt"
MI_XCI_FILES_TXT = "mi_xci_files.txt"

PINS_TXT = "pins.txt"
PIN_X_TXT = "pins.{}.txt"
PROPERTIES_TXT = "properties.txt"
ENCODING = "utf-8"


def read_list(path: Path) -> Iterator[str]:
    with path.open(encoding=ENCODING) as f:
        for pin_name in f:
            pin_name = pin_name.strip()
            if pin_name != "":
                yield pin_name


def read_value(path: Path) -> str:
    values = list(read_list(path))
    assert len(values) == 1
    return values[0]


def read_properties(path: Path) -> Dict[str, str]:
    props = {}
    with path.open(encoding=ENCODING) as f:
        for line in f:
            words = list(map(str.strip, line.split(maxsplit=3)))
            assert len(words) in [3, 4]
            if words == ["Property", "Type", "Read-only", "Value"]:
                continue
            assert words[1] in ["bool", "enum", "string", "string*"]
            assert words[2] in ["true", "false"]
            key = words[0]
            value = "".join(words[3:])
            props[key] = value
    return props


class BdCell(Module):
    def __init__(self, export_dir: Path):
        self.inputs: Dict[str, Signal] = {}
        self.outputs: Dict[str, Signal] = {}
        self._glue: Dict[str, Signal] = {}
        for pin_name in read_list(export_dir / PINS_TXT):
            pin_props = read_properties(export_dir / PIN_X_TXT.format(pin_name))
            self._import_pin(pin_props)

        cell_props = read_properties(export_dir / PROPERTIES_TXT)
        self._instance(cell_props)

    def _import_pin(self, pin_props: Dict[str, str]) -> None:
        assert "NAME" in pin_props
        assert "DIR" in pin_props
        assert "TYPE" in pin_props
        assert "LEFT" in pin_props
        assert "RIGHT" in pin_props
        assert "DEFAULT_DRIVER" in pin_props

        pin_name = pin_props["NAME"]
        assert pin_name != ""
        pin_dir = pin_props["DIR"]
        pin_dir_to_collection = {"I": self.inputs, "O": self.outputs}
        assert pin_dir in pin_dir_to_collection
        collection = pin_dir_to_collection[pin_dir]
        assert pin_name not in collection

        pin_type = pin_props["TYPE"]
        pin_type_to_importer = {
            "undef": self._import_pin_undef,
            "intr": self._import_pin_intr,
            "clk": self._import_pin_clk,
            "rst": self._import_pin_rst,
        }
        assert pin_type in pin_type_to_importer
        importer = pin_type_to_importer[pin_type]
        collection[pin_name] = importer(pin_props)

    def _import_pin_undef(self, pin_props: Dict[str, str]) -> Signal:
        assert set(pin_props["LEFT"]).issubset(digits)
        assert set(pin_props["RIGHT"]).issubset(digits)
        assert set(pin_props["DEFAULT_DRIVER"]).issubset("01")

        pin_name = pin_props["NAME"]
        left = int(pin_props["LEFT"] or 0)
        right = int(pin_props["RIGHT"] or 0)
        width = left - right + 1
        assert width > 0

        default = pin_props["DEFAULT_DRIVER"]
        if default == "":
            signal = Signal(bits_sign=(width, False), name=pin_name, reset_less=True)
        else:
            signal = Signal(bits_sign=(width, False), name=pin_name, reset=int(default, 2))
        signal_shifted = Signal(
            bits_sign=(width, False), name=f"{pin_name}__SHIFTED", reset_less=True
        )
        # Port indices in Vivado metadata do not change the packed connection
        # width: a vendor port [15:8] connects to an eight-bit Migen signal.
        # The instance owns outputs, while the surrounding gateware owns inputs.
        # Driving both directions from the instance-side signal leaves inputs
        # disconnected (and can create multiple drivers on the public signal).
        if pin_props["DIR"] == "I":
            self.comb += signal.eq(signal_shifted)
        else:
            self.comb += signal_shifted.eq(signal)

        self._glue[pin_name] = signal

        return signal_shifted

    def _import_pin_intr(self, pin_props: Dict[str, str]) -> Signal:
        return self._import_pin_undef(pin_props)

    def _import_pin_clk(self, pin_props: Dict[str, str]) -> Signal:
        assert pin_props["LEFT"] == ""
        assert pin_props["RIGHT"] == ""
        assert pin_props["DEFAULT_DRIVER"] == ""

        return self._import_pin_undef(pin_props)

    def _import_pin_rst(self, pin_props: Dict[str, str]) -> Signal:
        assert pin_props["LEFT"] == ""
        assert pin_props["RIGHT"] == ""

        return self._import_pin_undef(pin_props)

    def _instance(self, cell_props: Dict[str, str]) -> None:
        assert "CONFIG.Component_Name" in cell_props

        name = cell_props["CONFIG.Component_Name"]

        pin_mapping = {}
        for pin_name in self.inputs:
            signal = self._glue[pin_name]
            pin_mapping[f"i_{pin_name}"] = signal
        for pin_name in self.outputs:
            signal = self._glue[pin_name]
            pin_mapping[f"o_{pin_name}"] = signal

        self.specials += Instance(name, **pin_mapping)


class XilinxPlatformAuto(XilinxPlatform):
    def __init__(self, vivado_build_dir: Path):
        part = read_value(vivado_build_dir / MI_PART_TXT)
        super().__init__(part, [], name="genesys_zu-5ev", toolchain="vivado")
        self.ips: set[str] = set()

        self.add_platform_command("set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]")

        self.bd_cells: Dict[str, BdCell] = {}
        for bd_cell_name in read_list(vivado_build_dir / MI_BD_CELLS_TXT):
            assert bd_cell_name not in self.bd_cells
            self.bd_cells[bd_cell_name] = BdCell(vivado_build_dir / bd_cell_name)

        for xci_file in read_list(vivado_build_dir / MI_XCI_FILES_TXT):
            self.add_ip(xci_file)

    def import_submodules_to(self, module: Module) -> None:
        for bd_cell_name, bd_cell in self.bd_cells.items():
            setattr(module.submodules, bd_cell_name, bd_cell)

    def create_programmer(self) -> Never:
        raise NotImplementedError()
