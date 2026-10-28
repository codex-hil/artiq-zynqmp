# Status-only observer contract — 2026-10-28

Offline parser and contract only; no actual register read or executor. Three
synthetic examples illustrate active/sleep/failed observations. Every output
refuses continuous-sleep/RAM/recovery/deployment claims. Four test methods cover
states, failed-read plausible-output rejection, exact schema/nonce/address/types,
caller claim injection, input immutability and unconditional RAM refusal.
See docs/PIT_SLEEP_OBSERVER_CONTRACT.md. Hardware/profile gates unchanged.
Next safe offline step maps exact candidate wake/exception/reset/debug sources;
no physical poll or old RAM probe reuse follows from this result.
