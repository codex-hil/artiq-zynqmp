# KASLI04 bounded TCP readiness and clock-switch progress

Connect-only readiness is explicit opt-in, bounded to45seconds/15attempts;
this trial used40seconds. No commands are replayed by readiness. Two offline
tests cover delayed success, hard deadline, fast refusal cap and retaining
the connected object. All15 existing Kasli tests passed.

First physical trial connected after5.009s (one timeout), but closing that
probe and immediately reconnecting was refused. Second trial retained the
successful connection (5.049s) for the first real negative command; negative
commands, recovery and RAM download succeeded. First runtime boot command
executed the Si5324 clock setup and expected restart back into netboot.
Second download connection then timed out: runtime startup/management/RPC
were not reached. No DRTIO qualification.

Both trials restored diagnostic and retained mode10; second also restored
volatile clock/profile/PLL/frequency PASS. Leases released, no Genesys/other
Kasli/flash/OTP/SD access. No root cause of intermittent network proven.

Next code applies the same bounded retained-connection readiness to the
post-clock-switch second upload, default behavior unchanged. This extension
passed existing startup/panic tests and compilation, not yet run physically.
Runtime-upload evidence now remains true after initial acknowledgement even
if later startup fails. No admission/panic/clock checks bypassed.
