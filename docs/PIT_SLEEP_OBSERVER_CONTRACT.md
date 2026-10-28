# PMU sleep status observer contract — offline only

The parser interprets one caller-supplied GLOBAL_CNTRL sample. It contains no
capture function, MMIO backend, debug call, hardware executor or CLI. Version1
requires exactly version/nonce/address/return_code/value; expected nonzero64-bit
nonce must match and address must be0xffd80000. Booleans are not integers here.
Zero transport return plus a u32 value yields ACTIVE_SAMPLED or SLEEP_SAMPLED
from bit16. Failed transport requires value=null and yields UNKNOWN. Failed
reads carrying plausible output values are rejected. Other register bits are
retained only as caller data and confer no permission. Samples are unauthenticated.

The [UG1087 register definition](https://docs.amd.com/r/en-US/ug1087-zynq-ultrascale-registers/GLOBAL_CNTRL-PMU_GLOBAL-Register)
provides sampled state semantics. It does not reserve a no-wake interval. Every
parser result keeps continuous_sleep_proven, pmu_ram_access_allowed,
recovery_qualified, deployable and hardware_executed false. The separate RAM
admission function always refuses, including caller-supplied success overrides.
There is deliberately no mechanism for a parsed status to open the hardware gate.

Any future status-only physical observer first needs the verified owning station,
exact cable and shared Genesys lease for its entire lifecycle; a reviewed master/
security route and no-wake side effects; one aligned32-bit read of this register;
no writes/RMW, RAM access, PMU debug stop/step/register reads, IPI, reset, policy
changes or automatic retry. It must record transport failure without attempting
a different access route. These are review prerequisites, not a runnable plan or
admission. No physical read is authorized by this document alone.

A sleep sample cannot close exception/reset/debug/wake races across a later RAM
transaction. Safe RAM access requires separate evidence of continuous lifetime
ownership and independent recovery from a stuck transaction; neither exists in
this contract. Host timeout and cooperative IPI are insufficient. No firmware,
mailbox or older physical probe is changed.

Next safe offline work: map the exact candidate's wake/exception/reset/debug
sources to the proposed interval, using existing platform/source audits. Keep
unknown sources explicit and do not disable them to manufacture a quiet result.
