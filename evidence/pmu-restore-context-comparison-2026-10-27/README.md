# Restoration-context comparison — 2026-10-27

Retained guard snapshot PASS vs post-AIB restoration FAIL use exactly the same
PMU ELF34652786...4b6764b and no-master PLdf35fe96...8912d. Both guard records
show MSR80000106->80000104 and GPO0=0. Comparison fields/inputs are hash bound.
The failed trial additionally performed eight readonly AIB accesses. These runs
are not randomized/time-matched and do not prove the reads caused the failure.
Failure at first dow RAM write has no old register-channel probe or PC trace.
Normal-PMU r0/download qualification later PASS in a different execution context.

Next planned discriminating trial uses same guard firmware but explicitly no AIB
capture, changed r0-gated restoration and seven ordered stage checks. This adds
new observations before memory write; it is not claimed to fix root cause.
No physical trial occurred during comparison. Previous failure remains intact.
