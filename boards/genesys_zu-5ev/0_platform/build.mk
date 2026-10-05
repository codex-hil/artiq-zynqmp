PLATFORM := $(THIS)

I_PLATFORM := $(I)/$(PLATFORM)
I_PLATFORM_wildcard_TCL := $(wildcard $(I_PLATFORM)/*.tcl)
I_VIVADO_SCRIPT_TCL := $(I_PLATFORM)/vivado_script.tcl

O_PLATFORM_XSA := $(O)/platform.xsa

.PHONY: $(PLATFORM)
all: $(PLATFORM)
$(PLATFORM): $(O_PLATFORM_XSA)

$(O_PLATFORM_XSA): $(I_PLATFORM_wildcard_TCL) $(I_VIVADO_SCRIPT_TCL) | $(O) check-variant
	env -C "$(O)" -- vivado -mode batch -script "$(I_VIVADO_SCRIPT_TCL)" -tclargs "$(VARIANT)"
