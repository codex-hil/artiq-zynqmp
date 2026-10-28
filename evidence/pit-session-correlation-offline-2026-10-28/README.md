# Session/image/terminal correlation — 2026-10-28

Offline caller-fed Session binds expected nonzero nonce/image SHA to supplied
terminal snapshots and sample bytes using the existing strict receipt decoder.
A terminal correlation attempt is consumed before validation. Mixed nonce/image/
sample hashes, torn snapshots and duplicates reject and invalidate lifetime;
a later valid sleep sample cannot repair it. Closed sessions reject receipt use.
Valid terminal content, including error statuses, is recorded separately from
lifetime validity. Returned nested reports are fresh copies.

No physical sample or terminal origin is authenticated; content hashes are
bindings, not origin proof. No chronological ordering is established between
supplied terminal and status data. All reports keep sleep/RAM/deployment/HW and
destructive permissions false. Existing hardware gates remain unchanged. No
transport/executor/actual status read, policy change or hardware access occurred.
Four new test methods cover matching data, mixed/torn bindings, six event classes,
late-sleep/receipt nonresurrection, duplicates, errors, closure and report mutation.
Synthetic trace explicitly shows valid content after wake retaining invalidation.

Next safe offline step: replay archived actual-C fake-transport traces through
this correlator, checking error outcomes and deliberately mixed session/image
inputs. This remains software evidence and cannot admit a physical operation.
