# Bounded base-SPD reader preparation

Status: **offline orchestration controls PASS; AMD adapter candidate compiles; vendor-ISR integration and hardware NOT_RUN**.
No deployment command is provided yet. This does not qualify DDR.

`spd_reader.h` is transaction orchestration, not an I2C controller driver.
The candidate `spd_xiicps.h` reuses AMD XIicPs nonblocking begin/master ISR
callbacks; integration admission is still pending. The current vendor `MasterRecvPolled` calls `MasterPolledRead`, whose
receive wait has no local deadline. A caller-side deadline cannot interrupt a
blocked vendor call. Do not bind that API to these callbacks.

The caller must prove exclusive I2C1 ownership and a **known lower-page baseline**
before admission. The existing FSBL reader leaves the upper page selected; simply
calling this reader after FSBL is therefore not admitted. Page identity/state
establishment and adapter integration remain open. No unknown page is silently
assumed or called restored.

The fixed sequence is lower-page select (`0x36`, one zero byte), SPD offset zero
(`0x51`, one byte), receive128bytes, offset zero, receive128bytes, then lower-page
cleanup. No other addresses, mux operations, EEPROM data programming, bus clear,
retries or upper-page selection. Each stage has100ms budget and10000poll limit;
clock reversal/overflow fail. `tick` must receive monotonic microseconds and the
callbacks themselves must be bounded. On failure, attempt one cleanup only when
the adapter confirms both bus idle and no outstanding transfer/callback. A busy
or unknown state ends with `page_restored=0`, requiring outer recovery; never
force the bus idle. The outer lease and timeout must cover recovery/restoration.

Accept a capture only when `stopped && result == SPD_PASS && page_restored`.
Raw bytes must be retained, then CRC and independent controller geometry checked.
Matching two captures is not a CRC check or proof of physical capacity.

Host controls (fake transport, no HW):

```sh
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
  tests/test_spd_reader.c -o /tmp/artiq-test-spd-reader
/tmp/artiq-test-spd-reader
```

Controls cover refused admission, exact addresses/lengths, equal/mismatched
captures, each of six begin/completion failures, cleanup failure, elapsed/poll
limits and busy-bus cleanup refusal. They do not test an AMD driver or timing on
silicon. Next audit nonblocking AMD entry/handler paths, bind the callbacks,
compile against the existing BSP and test adapter failure handling before any
bounded physical acquisition with mandatory normal ARTIQ restoration.

## AMD adapter candidate

`spd_xiicps.h` uses `XIicPs_MasterSend/MasterRecv` and manually services
`XIicPs_MasterInterruptHandler`; no concurrent GIC dispatch is permitted. Bind
requires a caller assertion of exclusive/no-GIC ownership, initialized I2C1
0xff030000, platformZynqMP, seven-bit/non-repeated-start mode and idle bus. This
assertion is a precondition, not independently verified IRQ routing. Callbacks
are replaced; controller/GIC/callback snapshot/restoration is not implemented.
No repeated bind/reuse after error/timeout before outer restoration.

Unexpected events (including completion+NACK), residual byte counts or an error
poison the adapter. While pending, active state prevents cleanup even if hardware
bus busy clears. Completion requires correct event, zero residual count and idle
bus, then disables peripheral IRQs. Outer timeout/recovery remains necessary.
Source review distinguishes the legacy Zynq FIFO-wait branch from ZynqMP. This
is not yet a complete call-graph/timing proof of the actual AMD ISR.

Host adapter controls (mocked AMD APIs; vendor ISR not executed):

```sh
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
  -Itests/spd_stubs tests/test_spd_xiicps.c -o /tmp/artiq-test-spd-adapter
/tmp/artiq-test-spd-adapter
```

A translation unit including the adapter and calling `spd_amd_bind` compiled
with ARM GNU13.2 `aarch64-none-elf-gcc`, real qualified BSP includes, C11 and
`-Wall -Wextra -Werror`. This is compilation only, not a linked executable.
Next test the actual vendor ISR/call graph against a register model and complete
page/controller/IRQ/callback restoration before creating a physical wrapper.
