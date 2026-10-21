PYTHON ?= python3
VIVADO ?= vivado
.PHONY: test hdl build-trenz-reference

test:
	$(PYTHON) -m pytest -q gateware/test_mode3.py
	$(PYTHON) tools/check-old-wiring-regression.py

hdl:
	cd gateware && $(PYTHON) generate-fabric.py --spi-console --subclass 0 --native-8b10b --hd 1 --slow-6144

build-trenz-reference: hdl
	cd gateware && $(VIVADO) -mode batch -nojournal -log reference-build.log -source build-slow6144.tcl
