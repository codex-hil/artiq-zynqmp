I := .
O := build
.DEFAULT_GOAL := all

override I := $(abspath $(I))
override O := $(abspath $(O))

CONFIG := debug
VARIANT ?= blinker
ifneq ($(filter $(VARIANT),blinker local-rtio),$(VARIANT))
$(error VARIANT must be blinker or local-rtio)
endif

.PHONY: check-variant
check-variant: | $(O)
	@if test -f "$(O)/variant.txt"; then \
	  test "$$(cat "$(O)/variant.txt")" = "$(VARIANT)" || \
	  { echo 'Use a separate O= directory for each VARIANT.' >&2; exit 1; }; \
	else printf '%s\n' '$(VARIANT)' > "$(O)/variant.txt"; fi

.PHONY: all
all:

$(O):
	mkdir -- "$(@)"

THIS = $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))
include $(wildcard */build.mk)
