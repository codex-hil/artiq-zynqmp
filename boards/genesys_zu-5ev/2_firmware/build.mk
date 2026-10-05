FIRMWARE := $(THIS)

I_FIRMWARE := $(I)/$(FIRMWARE)

O_CARGO_BUILD := $(O)/cargo-build
O_RUST_FW_DIR := $(O_CARGO_BUILD)/armv7r-none-eabihf/$(CONFIG)
O_LIBRUST_FIRMWARE_A := $(O_RUST_FW_DIR)/librust_firmware.a
O_LIBRUST_FIRMWARE_D := $(O_RUST_FW_DIR)/librust_firmware.d

.PHONY: $(FIRMWARE)
all: $(FIRMWARE)
$(FIRMWARE): $(O_LIBRUST_FIRMWARE_A)

$(O_LIBRUST_FIRMWARE_A): $(I_FIRMWARE)/Cargo.toml $(I_FIRMWARE)/Cargo.lock $(I_FIRMWARE)/.cargo/config.toml
	env -C "$(I_FIRMWARE)" -- cargo build --locked --target-dir="$(O_CARGO_BUILD)" \
	  --profile="$(subst debug,dev,$(CONFIG))"
-include $(O_LIBRUST_FIRMWARE_D)
