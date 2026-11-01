# Own compiler-intermediate storage inventory — offline2026-11-01

LGPL-3.0-or-later. Inventory only; no hardware, files deleted/moved or threshold
changes. Does not claim no reclaimable files exist elsewhere in the workspace.

Examined own dated pit-* build directories:165 primary objects/3,207,168 allocated
bytes and108 LTO intermediates/56,369,152 bytes. All are on system device66306;
affected shared data is device2049. Cleaning these would not repair shared restore
capacity, so they were retained. Project scripts/tests bytecode2,621,440 bytes is
insufficient and shared ownership is not presumed. Source/evidence/git/frozen
snapshots, ELF/maps/build records, vendor/tool/install caches, .Xil/Vivado logs
and other-thread projects remain untouched.

Shared free1,287,483,392 bytes vs strict reserve+minimum1,342,177,280: deficit
54,693,888 bytes (~52.2MiB). Capacity is a sampled value, not a reservation. Full
recovery/programming admission requires rerunning storage checks and allocating
existing reserve; do not move reserve to another filesystem or reduce thresholds.
Existing155 software tests unchanged/not rerun. No device lease acquired/needed.

Human storage/ownership action now required for dependent recovery/HW trials:
free at least the deficit on /srv/codex-hil-data (128MiB suggested margin), or
identify a specific owner-approved directory there to archive/move. We do not
select another project's data for deletion. No automatic supervisor continuation
for the blocked recovery path. After storage change, recheck free space/reserve,
then separately resume readiness; this does not admit handler/vector/power trials.
