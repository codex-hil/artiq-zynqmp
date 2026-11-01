# ROM/loader static interface checkpoint —2026-11-01

LGPL-3.0-or-later. No loaders executed/hardware/ROM/PMU RAM read/remap/reset/vector
change. Initial RAM extension table0xffddf6e0/256 entries all-zero in ELF; absolute
ROM service declaration0xffd07bc8 and loader command text pinned. Dynamic power
hook assignment exists, so initial zero data is not live no-hook proof. No actual
ROM code/PC/vector selection observed. See docs/PIT_ROM_LOADER_REVIEW.md.

Existing155-test suite unchanged/not rerun; static-source/artifact review only.
Next safe offline: readiness/decision matrix and non-executing qualification
proposal, separating approved offline evidence from policy-changing/HW actions.
No new trial, exception-entry/notification/recovery/sleep or deployment admission.
