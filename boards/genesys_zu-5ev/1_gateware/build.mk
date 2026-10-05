GATEWARE := $(THIS)

I_GATEWARE := $(I)/$(GATEWARE)
I_GATEWARE_wildcard_PY := $(wildcard $(I_GATEWARE)/*.py)
I_GATEWARE_PY := $(I_GATEWARE)/gateware.py

O_MIGEN_BUILD := $(O)/migen-build
O_TOP_BIT := $(O_MIGEN_BUILD)/top.bit

.PHONY: $(GATEWARE)
all: $(GATEWARE)
$(GATEWARE): $(O_TOP_BIT)

$(O_TOP_BIT): $(O_PLATFORM_XSA) $(I_GATEWARE_wildcard_PY) $(I_GATEWARE_PY) | check-variant
	env -C "$(O)" -- "$(I_GATEWARE_PY)" -B "$(O)" -M "$(O_MIGEN_BUILD)" --variant "$(VARIANT)"
