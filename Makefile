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
