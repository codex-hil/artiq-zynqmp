# Isolated reset management candidate

The management clock and registers must remain live while PS PL ingress, master,
RX and RTIO target domains reset. This is a separate AXI-Lite interface at
`0xb0000000`; the real parent AXI address decoder is not implemented yet.
It must bypass the target admission gate and target reset. Address identity
alone does not establish that a deployed bitstream contains this ABI.

| Offset | Register | Meaning |
| --- | --- | --- |
| 0 | identity, read only | `0x47524d31` |
| 4 | command | bit0 reset request; bit1 requester abandoned; reset value1 |
| 8 | status, read only | bit0 reset held; bit1 fresh abandonment ready; bit2 admitted |

Aligned full32bit writes to command only, values0..3. Invalid addresses, other
writes, reserved bits and partial writes return SLVERR. Unaligned access is not
qualified. Status bits cross independently: use the ordered protocol, not an
assumption that the entire status vector is an atomic snapshot.

1. Verify identity. Stop issuing new target MMIO and coordinate all requesters.
2. Write command1 and poll with a finite limit until reset held and not admitted.
3. Record outstanding target operations as outcome unknown. Discard local pending
   completion expectations; reset does not undo an external write or authorize retry.
4. Write command0, then poll for reset held and fresh abandonment ready.
5. Write command2 and poll until reset released and admitted. This acknowledges
   requester abandonment; it is not a target-write rollback assertion.
6. Reinitialize target protocol state and begin fresh traffic. Never resume an
   old partial AUX frame or automatically replay an unacknowledged command.

On timeout, do not reopen admission or retry target operations. Keep/request reset
and diagnose missing clocks/readiness offline or with authorized board leases.
No automatic clock-loss watchdog, management-domain reset recovery, physical CDC
constraints or real firmware implementation is claimed by this candidate.

The stock shared AXIDecoder is explicitly refused for this placement: an
accepted target AW with a missing B retains its write-direction slave lock,
blocking a later management reset write. Independent status reads do not solve
reset-write reachability. Independent PS ingress or an explicitly qualified
transaction-abort protocol is required; neither has been implemented yet.

Current deployed platform still disables GP1. The isolated Dell Vivado PS IP
query enabled GP1 and reported HPM1 AXI32/address40/ID16 with a separate clock
input. Its connected address probe was assigned `0xb0000000` (HPM0 probe:
`0xa0000000`). The former management base `0xa0020000` is superseded.
This is IP/address inspection, not validated BD, synthesized wrapper or board
proof. Actual scalar exported-pin helper integration remains to be verified.

The dual-ingress model now verifies management reset writes with an unaccepted
target B response, using two independent behavioral initiators. This does not
prove that one A53 core stalled on a synchronous target MMIO access can issue
management commands. An independent recovery execution context or a separately
qualified bounded-fault mechanism is required; no core has been reassigned.

Current ownership review preserves CPU0 foreground network/debug services and
CPU1 CoreDMA worker. CPU2/3 are not assigned or qualified recovery agents.
`a53/reset_driver.h` is a callback-based portable API tested on the host only.
Its finite polling does not bound a callback blocked inside real MMIO. It reports
reset/release attempts before writes, including failures after a write may have
executed. Success still requires target reinitialization and does not clear the
unknown outcome of prior operations. Existing direct A53 bindings are unchanged.

## Stopped RX and stale status (2026-11-08)

The functional composition test suppresses RX and its release-domain clock edges
after admission opens. With ready, reset-done, active and aligned retained high,
admission stays open. Neither the coordinator nor the link boundary detects clock
loss. These levels cannot authorize unattended recovery or prove a live RX clock.

An explicit request from the independent control clock closes admission. With the
functional reset substitute, RX acknowledgement remains stale until RX restarts;
fresh requester abandonment alone does not reopen the path. After restart, the
reset acknowledgement clears and fresh release acknowledgements permit reopening.
This verifies sequencing only. It does not qualify asynchronous reset assertion
with a stopped physical clock, packet recovery, or recovery by a CPU hung on MMIO.

Before hardware admission, qualify a separate clock-loss indication/interlock or
a bounded externally managed fault protocol. The existing userclk-active signal
is not a watchdog. Next offline work is original vendor userclk helper simulation
with a stopped source clock. No production constraint or RTL change is adopted.

## Userclk-active qualification and next candidate

The original vendor RX userclk helper, using AMD's BUFG_GT simulation library at
ratio1, retains active high when the ideal source stops. Reset clears active
without source edges, and restart is required to set it again. This confirms the
status is not a clock-loss watchdog; it does not qualify real GT failure behavior.

The next isolated candidate must observe RX progress from the independently live
control clock. It must begin closed, require fresh progress before admission,
latch loss after a specified finite observation interval, and keep admission
closed after spontaneous RX restart until explicit reset/rearm completes. CDC
encoding, sampling aliasing, allowable clock ratios, reset epochs and timeout
selection must be stated and tested. A monitor fault must not depend on a working
RX edge or a CPU completing target MMIO. The independent management ingress must
remain usable; committed writes retain unknown outcome and must not be retried.

These are requirements for offline design and review, not an implemented watchdog
or permission to resume hardware operations. No threshold has been qualified for
the physical link, and the existing maintenance hold remains.

## Functional monitor/reset composition (2026-11-08)

Test-local wiring gates admission with both coordinator admission and qualified
RX progress. Coordinator reset rearms the monitor; only the explicit management
request drives the coordinator request. A monitor fault does not drive reset.
This avoids a feedback path in which a fault would trigger its own rearm and clear
the sticky fault. No automatic retry or transaction-outcome inference is added.

Stopped RX with stale high status closes effective admission. Spontaneous clock
return leaves it closed. Explicit reset, fresh abandonment, reset-domain
acknowledgements and fresh progress are all needed before reopening. The link
boundary follows through its existing synchronizers, so this is not an immediate
asynchronous packet cutoff claim. This composition is in a test fixture only.
The complete AXI/management path and physical clock-loss behavior remain pending.

## Spontaneous fault during pending AXI response: adoption refused

The full CSR/AUX/PS CDC test commits length68 (native17 words), leaves BVALID
unaccepted, then stops RX clock edges. A test-local outer gate closes all five
channels when the progress monitor faults. Independent HPM1 remains usable for
identity reads and explicit management reset; reset/rearm allows a fresh write12.

The inner pending BVALID remains asserted but the outer gate hides it. This
withdraws an external response before its handshake or an explicit completed
reset. It does not satisfy normal AXI VALID retention. The existing gate's
in-flight disable contract requires requester abandonment and coordinated reset;
a spontaneous clock fault alone establishes neither. This wiring is refused for
production adoption even though containment and explicit recovery tests pass.

Next design work must separate admission of new requests from retention/draining
of existing responses and explicit reset containment. Partial AW-only and W-only
transactions also require treatment. No missing response may imply rollback or
automatic retry: the test observes the original committed register effect.

## Partial-write coordinated reset checks (2026-11-09)

Two full CSR/AUX/dual-HPM functional tests accept only AW or only W68, then stop
RX, abandon the operation and issue explicit reset through HPM1. The drain bridge
shares the PS reset with the target converter; all target domains participate in
the existing acknowledgement sequence. After fresh release and progress, no old
B response appears for30 cycles, length reads0, and a fresh write12 reads back12.
The old partial write is not combined with the fresh transaction in these tests.

This evidence applies only to coordinated bridge-and-target reset. Resetting one
side alone can leave a half-transaction resident elsewhere and is not an admitted
recovery procedure. Negative-control tests of each independent reset remain next.
No hardware, physical reset, or recovery by the same hung CPU is qualified.
