# Concrete MMIO composition LTO integration — offline, 2026-10-30

Fresh11-unit custom C/LTO audit link uses newly added pit_mmio_composition_audit
instead of the old generic audit entry. It requires a plan/read adapter, NULL
capture context, unset raw read callback and unconsumed plan, then binds
pit_mmio_read and calls the composition model. It always ends in the terminal
audit loop. There is no PMU main/request hook or runnable capture/consumer.
Other callbacks and image/sample digests remain caller supplied and untrusted.

Actual linked raw callback retains one device lwi and one output swi. Scoped
entry/raw/forwarder word-store checks PASS; no undefined symbols. Layout PASS:
telemetryffdd8860/32; stackffddce3c..ffddde40;6304bytes below extension table.
Frames entry292/readforwarder52/raw0 ->344bytes internal subtotal, not total
caller/other callbacks/exception stack. Static layout/store width do not prove
all addresses safe, liveness or fault/ROM/wake policy. Native RWE legacy flags
remain unchanged. Vendor objects and BSP/runtime archives are reused.

Both old forwarded-v1/ro-context-v2 flow selections reject this separate entry;
old gates/sources/snapshots remain unchanged. New full flow/binding mutation
checker is NOT yet qualified.78 PIT tests PASS (existing host behavior); this
new audit C file was compiled/linked and statically inventoried, not physically
executed. No hardware access, PMU RAM read, firmware deployment or DDR admission.

build.py refuses overwrite and preserves sources/link commands in build.json.
Next safe offline step: qualify a separate MMIO-profile flow checker against
actual linked binding-prefix/address/raw-load/output words and hostile mutations,
then define its complete source/helper closure. No physical trial follows yet.
