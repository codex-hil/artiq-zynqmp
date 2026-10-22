# Bounded base-SPD reader preparation

Status: **offline orchestration controls PASS; AMD adapter, build and hardware NOT_RUN**.
No deployment command is provided yet. This does not qualify DDR.

`spd_reader.h` is transaction orchestration, not an I2C controller driver.
The future adapter must reuse maintained AMD XIicPs, with nonblocking begin/poll
callbacks. The current vendor `MasterRecvPolled` calls `MasterPolledRead`, whose
receive wait has no local deadline. A caller-side deadline cannot interrupt a
blocked vendor call. Do not bind that API to these callbacks.

The caller must prove exclusive I2C1 ownership and a **known lower-page baseline**
before admission. The existing FSBL reader leaves the upper page selected; simply
calling this reader after FSBL is therefore not admitted. Page identity/state
establishment and the exact AMD adapter remain open. No unknown page is silently
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
