# Isolated reset management candidate

The management clock and registers must remain live while PS PL ingress, master,
RX and RTIO target domains reset. This is a separate AXI-Lite interface at
`0xa0020000`; the real parent AXI address decoder is not implemented yet.
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

Independent HPM1 is now a source-only candidate. Current platform disables GP1.
The management base `0xa0020000` is provisional: its reachability through HPM1
must be established from actual PS IP address segments before integration.
Synthetic exported-pin tests do not prove actual IP port names or widths.
