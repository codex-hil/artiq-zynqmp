# KASLI04 network recheck after user confirms switch link

User confirms SFP connection to switch and lit switch link LED. Bounded
guarded master trial again passes bootloader CRC/SDRAM/memory test, but
netboot TCP times out before runtime upload. Clock profile unchanged.
Diagnostic and final retained mode10 restoration PASS; leases released.
No Genesys/other Kasli/flash/OTP/SD access.

During the leased session, host-only `ip -j -6 neigh` inspection showed
fe80::4b:4ff:fe70:4854 at02:4b:04:70:48:54 REACHABLE on enp2s0. This
observation was returned to the tool transcript, not saved as a raw file.
It indicates neighbor reachability, not successful TCP service or runtime.
Do not label this trial a proven cable-disconnection failure.

Next wrapper change records TCP connect/send/close-receive stage plus
filtered neighbor-cache state on error before restoring hardware. No
new test performed with that instrumentation in this checkpoint.
