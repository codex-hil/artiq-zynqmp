.DEFAULT_GOAL := test
PYTHON ?= python3
O ?= build-host
ARTIQ_SOURCE ?= $(CURDIR)/common/artiq
export PYTHONPATH := $(ARTIQ_SOURCE):$(CURDIR)/common/migen$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: test test-sim firmware diagnostics test-hw test-hw-uart hdl test-kernel-abi
test: test-sim firmware diagnostics

test-sim:
	$(PYTHON) -m unittest discover -s tests -v

hdl:
	$(PYTHON) scripts/generate_rtio_hdl.py --output=$(abspath $(O))/local-rtio-hdl

firmware:
	$(MAKE) -C boards/genesys_zu-5ev 2_firmware O=$(abspath $(O))/original-r5 CONFIG=release

diagnostics:
	cd diagnostics/a53 && cargo build --release --locked --target-dir=$(abspath $(O))/a53
	$(PYTHON) scripts/validate_a53_elf.py $(abspath $(O))/a53/aarch64-unknown-none/release/genesys-a53-bringup

test-hw:
	$(PYTHON) scripts/test_rtio_hw.py $(if $(CSR_MAP),--csr-map=$(CSR_MAP)) --output=$(abspath $(O))/hardware-results.json

test-hw-uart:
	$(if $(SERIAL),,$(error Specify SERIAL= for the identified Genesys UART))
	$(PYTHON) scripts/capture_a53_uart.py --port=$(SERIAL) --output=$(abspath $(O))/a53-hardware-results.json

test-kernel-abi:
	$(if $(NAC3_SOURCE),,$(error Specify NAC3_SOURCE= checkout at the documented prototype revision))
	$(if $(ABI_TOOLS),,$(error Specify ABI_TOOLS= directory prepared by setup_abi_tools.py))
	$(PYTHON) scripts/test_kernel_abi.py --nac3-source=$(NAC3_SOURCE) --tools=$(ABI_TOOLS) --output=$(abspath $(O))/kernel-abi $(if $(ABI_ARTIQ_SOURCE),--artiq-source=$(ABI_ARTIQ_SOURCE) --sipyco-source=$(ABI_SIPYCO_SOURCE))

.PHONY: test-hw-jtag
test-hw-jtag:
	$(if $(JTAG_SERVER),,$(error Specify JTAG_SERVER= current hw_server URL))
	$(if $(JTAG_CABLE),,$(error Specify JTAG_CABLE= identified Genesys cable serial))
	$(if $(SERIAL),,$(error Specify SERIAL= identified Genesys UART))
	$(if $(A53_ELF),,$(error Specify A53_ELF= DDR diagnostic ELF))
	$(if $(PSU_INIT),,$(error Specify PSU_INIT= local-rtio generated psu_init.tcl))
	$(PYTHON) scripts/test_jtag_hw.py --server="$(JTAG_SERVER)" --cable="$(JTAG_CABLE)" --serial="$(SERIAL)" --elf="$(A53_ELF)" --psu-init="$(PSU_INIT)" --output="$(abspath $(O))/jtag-hardware"

.PHONY: test-hw-ethernet test-hw-ethernet-bringup
test-hw-ethernet:
	$(if $(BOARD_IP),,$(error Specify BOARD_IP= DHCP address reported by diagnostic UART))
	$(PYTHON) scripts/test_ethernet_hw.py --ip="$(BOARD_IP)" --output="$(abspath $(O))/ethernet-packets.json"

test-hw-ethernet-bringup:
	$(if $(JTAG_SERVER),,$(error Specify JTAG_SERVER= current hw_server URL))
	$(if $(JTAG_CABLE),,$(error Specify JTAG_CABLE= identified Genesys cable serial))
	$(if $(SERIAL),,$(error Specify SERIAL= identified Genesys UART))
	$(if $(PMU_ELF),,$(error Specify PMU_ELF= built PMU firmware))
	$(if $(FSBL_ELF),,$(error Specify FSBL_ELF= Piotr-patched FSBL firmware))
	$(if $(ETHERNET_ELF),,$(error Specify ETHERNET_ELF= AMD lwIP diagnostic))
	$(PYTHON) scripts/test_ethernet_bringup.py --server="$(JTAG_SERVER)" --cable="$(JTAG_CABLE)" --serial="$(SERIAL)" --pmu="$(PMU_ELF)" --fsbl="$(FSBL_ELF)" --elf="$(ETHERNET_ELF)" --output="$(abspath $(O))/ethernet-hardware"

.PHONY: test-services test-hw-services
test-services:
	cargo test --locked --lib --manifest-path boards/genesys_zu-5ev/2_firmware_a53/Cargo.toml --target-dir=$(abspath $(O))/services

test-hw-services:
	$(if $(BOARD_IP),,$(error Specify BOARD_IP= actual DHCP address))
	$(if $(ABI_ARTIQ_SOURCE),,$(error Specify ABI_ARTIQ_SOURCE= current upstream ARTIQ checkout))
	$(if $(ABI_SIPYCO_SOURCE),,$(error Specify ABI_SIPYCO_SOURCE= compatible sipyco checkout))
	$(PYTHON) scripts/test_a53_services_hw.py --ip="$(BOARD_IP)" --artiq-source="$(ABI_ARTIQ_SOURCE)" --sipyco-source="$(ABI_SIPYCO_SOURCE)" --output="$(abspath $(O))/services-hardware.json"
