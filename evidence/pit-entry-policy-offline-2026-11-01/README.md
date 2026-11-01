# Initial software config/entry policy checkpoint —2026-11-01

LGPL-3.0-or-later. Read-only initial ELF/BSP and official architecture review.
12 target offsetof assertions/sizeof PASS; no hardware/PVR/live MSR/vector-state
observation. See docs/PIT_ENTRY_POLICY_REVIEW.md for field values, exact source
links and limitations. BaseVectorAddr0xffd00000 differs from linked vectors
0xffdc0000; no patch/relocation attempted. No exception or break exclusion follows
from software config values. C_FAULT_TOLERANT unknown, conditional second-fault
halt is not guaranteed recovery. Existing155 tests unchanged/not rerun.

Next safe offline: trace original vendor vector/shadow/startup-selection code and
linked aperture assumptions without reading write-only GPO or changing vectors.
Current assembly candidate remains uninstalled, synthetic link non-PMU. No
notification/reentry/sleep/APB access/recovery/deployment admission.
