.DEFAULT_GOAL := test
PYTHON ?= python3
O ?= build-host
ARTIQ_SOURCE ?= $(CURDIR)/common/artiq
export PYTHONPATH := $(ARTIQ_SOURCE):$(CURDIR)/common/migen$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: test test-sim firmware diagnostics test-hw test-hw-uart hdl test-kernel-abi
test: test-sim firmware diagnostics

test-sim:
	$(PYTHON) -m unittest discover -s tests -v

.PHONY: test-hw-dma-engine
test-hw-dma-engine:
	$(if $(CSR_MAP),,$(error Specify DMA CSR_MAP=))
	$(if $(SERVER),,$(error Specify SERVER= for Genesys JTAG))
	$(PYTHON) scripts/test_dma_jtag_hw.py --csr-map=$(CSR_MAP) --server=$(SERVER) --cable=210383B7F02DA --output=$(abspath $(O))/dma-engine-hardware

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

.PHONY: test-hw-kernel-cpu1
test-hw-kernel-cpu1:
	$(if $(JTAG_SERVER),,$(error Specify JTAG_SERVER= current hw_server URL))
	$(if $(JTAG_CABLE),,$(error Specify JTAG_CABLE= identified Genesys cable serial))
	$(if $(SERIAL),,$(error Specify SERIAL= identified Genesys UART))
	$(if $(BOARD_IP),,$(error Specify BOARD_IP= actual DHCP address))
	$(if $(KERNEL_POSITIVE),,$(error Specify KERNEL_POSITIVE= hardware diagnostic directory))
	$(if $(KERNEL_NEGATIVE),,$(error Specify KERNEL_NEGATIVE= hardware negative-control directory))
	$(PYTHON) scripts/test_kernel_cpu1_hw.py --server="$(JTAG_SERVER)" --cable="$(JTAG_CABLE)" --serial="$(SERIAL)" --positive="$(KERNEL_POSITIVE)" --negative="$(KERNEL_NEGATIVE)" --ip="$(BOARD_IP)" --output="$(abspath $(O))/kernel-cpu1-hardware"

.PHONY: test-hw-network-kernel
test-hw-network-kernel:
	$(if $(BOARD_IP),,$(error Specify BOARD_IP= actual DHCP address))
	artiq-host python scripts/test_network_kernel_hw.py --rtio --ip="$(BOARD_IP)" --output="$(abspath $(O))/network-kernel"

.PHONY: test-hw-rtio-kernel
test-hw-rtio-kernel:
	$(if $(BOARD_IP),,$(error Specify BOARD_IP= actual DHCP address))
	artiq-host python scripts/test_network_kernel_hw.py --rtio --ip="$(BOARD_IP)" --output="$(abspath $(O))/rtio-kernel"

.PHONY: test-hw-ttl-loopback
test-hw-ttl-loopback:
	$(if $(BOARD_IP),,$(error Specify BOARD_IP= actual DHCP address))
	artiq-host python scripts/test_ttl_loopback_hw.py --ip="$(BOARD_IP)" --output="$(abspath $(O))/ttl-loopback"

.PHONY: test-hw-kernel-exceptions
test-hw-kernel-exceptions:
	$(if $(BOARD_IP),,$(error Specify BOARD_IP= actual DHCP address))
	artiq-host python scripts/test_kernel_exceptions_hw.py --ip="$(BOARD_IP)" --output="$(abspath $(O))/kernel-exceptions"

.PHONY: test-hw-core-dma
test-hw-core-dma:
	$(if $(BOARD_IP),,$(error Specify BOARD_IP= actual DHCP address))
	artiq-host python scripts/test_core_dma_hw.py --ip="$(BOARD_IP)" --output="$(abspath $(O))/core-dma"

# DRTIO PHY diagnostics: synthesis only, no programming of the board.
DRTIO_REFCLK_MHZ ?= 125
MISOC_SOURCE ?= /srv/codex-hil-data/artiq-zynqmp/reference/misoc-current
.PHONY: drtio-phy test-drtio-protocol
drtio-phy:
	mkdir -p "$(abspath $(O))/drtio-phy"
	cd "$(abspath $(O))/drtio-phy" && vivado -mode batch -source "$(CURDIR)/diagnostics/drtio/build_phy.tcl" -tclargs "$(abspath $(O))/drtio-phy/generated" "$(DRTIO_REFCLK_MHZ)" > build.log 2>&1
	$(PYTHON) diagnostics/drtio/check_phy_build.py "$(abspath $(O))/drtio-phy/generated" "$(abspath $(O))/drtio-phy/build.log" --output="$(abspath $(O))/drtio-phy/results.json"

test-drtio-protocol:
	mkdir -p "$(abspath $(O))/drtio-protocol"
	cd "$(abspath $(O))/drtio-protocol" && PYTHONPATH="$(abspath $(ARTIQ_SOURCE)):$(CURDIR)/common/migen:$(abspath $(MISOC_SOURCE))" $(PYTHON) -m unittest discover -s "$(abspath $(ARTIQ_SOURCE))/artiq/gateware/test/drtio" -t "$(abspath $(ARTIQ_SOURCE))" -v

.PHONY: drtio-top test-drtio-monitor test-hw-drtio-phy
drtio-top:
	$(if $(DRTIO_PS_EXPORT),,$(error Specify DRTIO_PS_EXPORT= existing Piotr PS export))
	$(if $(DRTIO_PHY_EXPORT),,$(error Specify DRTIO_PHY_EXPORT= validated GTH diagnostic IP export))
	PYTHON="$(PYTHON)" bash diagnostics/drtio/build_top.sh "$(DRTIO_PS_EXPORT)" "$(DRTIO_PHY_EXPORT)" "$(abspath $(O))/drtio-top"

test-drtio-monitor:
	PYTHONPATH="$(CURDIR)/diagnostics/drtio:$(CURDIR)/common/artiq:$(CURDIR)/common/migen:$(MISOC_SOURCE)" $(PYTHON) -m unittest discover -s diagnostics/drtio -p 'test_*.py' -v

test-hw-drtio-phy:
	$(if $(CSR_MAP),,$(error Specify diagnostic CSR_MAP=; original RTIO map is incompatible))
	$(if $(JTAG_SERVER),,$(error Specify JTAG_SERVER= current hw_server URL))
	$(PYTHON) diagnostics/drtio/test_phy_hw.py --csr-map="$(CSR_MAP)" --server="$(JTAG_SERVER)" --cable=210383B7F02DA --output="$(abspath $(O))/drtio-phy-hardware"

.PHONY: test-drtio-codec
test-drtio-codec:
	PYTHONPATH="$(CURDIR)/diagnostics/drtio:$(abspath $(ARTIQ_SOURCE)):$(CURDIR)/common/migen:$(abspath $(MISOC_SOURCE))" $(PYTHON) -m unittest discover -s diagnostics/drtio -p 'test_raw20_codec.py' -v
