# Linked private digest pipeline — offline 2026-10-31

LGPL-3.0-or-later. No hardware operations.

Fresh19-custom-C-unit small LTO audit link, reused vendor objects/BSP archives,
no undefined symbols. The new capture/digest function and fixed SHA are retained
as separate callable audit functions; existing IRQ root still calls the old
lifecycle/status composition. No new main/request hook or digest terminal binding.
Existing source/runtime/frozen image profiles unchanged.

Actual linked review: capture ffdd06f4/448 bytes/frame156, three direct calls:
collector ffdcc420, SHA ffdd0338, publisher ffdcbd58. Private record at stack+32
is passed to both hash and publisher; digest stack+80 is copied as words before
state valid=1 and publication. No library clear/copy call introduced here.
Collector specialized by LTO is312 bytes/frame92; publisher404 bytes/frame104.
SHA956 bytes/frame300 calls only local swap (12 bytes/frame0) as direct calls.
The64-word SHA constant table at ffdd4e60 (256 bytes) matches numerical source
constants as little-endian u32; hash recorded in sha-constants.json.

Word-store checker passes all five scoped functions. ELF layout and owned mailbox
checks pass. Call list in review.json records direct brlid targets, not a generic
CFG/transitive proof: collector/publisher still use indirect callbacks, and no
exception/error/debug/ownership/liveness behavior follows. Capture+SHA+swap peak
scoped frames156+300+0=456; capture+collector248 and capture+publisher260 exclude
callback stacks. These are scoped subtotals, not total-stack qualification.

Existing121-test Python result belongs to unchanged implementation tests from the
prior checkpoint; no new tests or physical claims. This step adds a fresh target
link and linked artifact inspections only. Local vendor-containing ELF stays out
of public Git; public build.json identifies source hashes/command/artifact digest.
Old exact gates intentionally do not qualify this changed image/address set.

Next safe offline step: separate lifecycle/composition API using the internally
produced sample digest, retaining failure statuses and final MSR observation after
hash execution. Test collector/hash/publication failure correlation and prevent
caller-supplied sample digest substitution. Then relink/review the distinct root.
No deployment, image-digest input protocol, authentication, PMU RAM reader lifetime,
exception exclusion or arbitrary-hang recovery is established by this audit.
