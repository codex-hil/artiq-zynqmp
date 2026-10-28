# Independent recovery mapping inventory — 2026-10-28

Read-only inventory after owner requested continuation. No SSH/device connection,
JTAG/UART/AP0/network action, reset or power operation. Reviewed local docs,
artifacts, environment-rebuild text and exact Genesys recovery records/scripts.
Pinned inputs and scoped findings are in review.json.

Existing restore is conditional on working PMU debug stop/suspended/r0/download/
resume. Historical normal recovery followed a user-reported reboot; actual POR
was not independently established. No verified Genesys-specific independent
power/reset actuator or wiring was found in this reviewed material. This is not
an assertion that none exists physically or in another private system.

Physical progress needs owner information: identify the connected independent
power/reset mechanism and its board mapping, or confirm availability of manual
physical power cycling if a candidate leaves debug inaccessible. That information
alone does not qualify a stuck-transaction recovery; its effect and full baseline
restoration still require review. No new physical test, automatic identical retry
or deployment is admitted. Existing software observer/session stage is complete.
