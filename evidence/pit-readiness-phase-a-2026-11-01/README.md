# Present read-only readiness —2026-11-01

LGPL-3.0-or-later. Actual read-only plug access/host metadata, not firmware test.

On greg-OptiPlex-3070/uid1001, Genesys shared flock and unique plug reservation
held together through5.324s bounded window. Plug reportsON; physical_state_confirmed
false and sample-age unknown retained. No power/on/off/reset/download/JTAG state
change/PMU memory/GPO access. Expected Digilent USB/UART serial metadata exists
(current ttyUSB4); UART NOT opened. Passive neighbor MAC matches historical core
but STALE, so no network probes or current runtime identity claim. Board lock and
plug reservation released; private token file removed after successful release.
No secrets/token in public evidence; device/runtime/voltage/POR not inferred.

All nine selected normal restore/PMU/FSBL input files exist and hash-match dated
manifest. Disk observed free root6.55GB, shared1,287,987,200 bytes. Existing restore
reserve805,306,368 plus normal minimum536,870,912 requires1,342,177,280: shared
short by54,190,080 bytes (~51.7MiB). No reserve allocated or threshold weakened.
Thus recovery/programming windows remain not admitted at this observation.

Next safe offline step: inventory only this thread's disposable compiler
intermediates to recover capacity while preserving ELF/maps/build/evidence/frozen
snapshots, vendor/tool/install caches and other-thread data. No arbitrary cleanup
or switching power to work around disk/identity limits. Current runtime identity,
cold recovery/entry/exception policy/sleep/recovery remain unqualified. No new
handler admission. Existing155 software tests unchanged/not rerun.
