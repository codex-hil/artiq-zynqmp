# Build input provenance review — 2026-10-28

Read-only offline inventory of current files referenced by the RO-context build.
All 18 custom source/header hashes match the frozen audit snapshot. Every
inventoried path exists: ten custom sources/objects/dependency lists, 60 vendor
sources, 70 link objects, ten unique archive paths from map LOAD entries, one
linker script, one specs file, four recipe/map/staging records and seven tools.
GCC identifies itself as 13.3.0. The archive paths are recorded as the map spells
them, with resolved paths separately; they are not claims about selected members.

1665 current header paths form an intentional superset, including toolchain/BSP
headers. Original -MMD dependency lists exclude system headers. This inventory
was taken after the build and cannot establish build-time bytes. Reused vendor
objects have a separate recipe with lab_guard_enabled=false and
vector_snapshot_enabled=false; ancestry is not independently established by
current hashes. Tool/shared-library/runtime closure is incomplete. No trusted
provenance or reproducible-build claim is made. Full gaps are in inventory.json.

collect.py reads current files and tool version/resolution only; rerunning prints
a fresh observation and does not modify the old report or any build output.
Validation checked no missing inputs, all 18 source matches, and 70/10 link/custom
object counts. No implementation changed; prior 60-test result is historical,
not a new suite run at this checkpoint. No HW access or admission change.

Next safe offline step: independently recompile the ten custom translation units
into a fresh directory with complete system-header dependency capture; compare
code sections and record any path/debug differences before claiming agreement.
This still will not close vendor/BSP ancestry, MMIO recovery or AP0 visibility.
