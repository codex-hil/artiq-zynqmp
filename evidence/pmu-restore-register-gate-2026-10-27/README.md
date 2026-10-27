# Pre-download PMU register-channel gate — 2026-10-27

Offline only. Compare prior vector-snapshot restoration PASS vs post-AIB capture
restoration FAIL: old helper emitted only final success marker; failure occurred
inside dow at first RAM address0xffdc0000. Stop and suspended-property gate had
passed, but no processor-register transaction was positively tested before write.
No evidence identifies root cause or proves AIB reads caused it. User reboot and
normal-runtime recovery subsequently PASS; do not reinterpret the old FAIL.

Changed bootstrap requires rrd -nvlist r0 after exact-target halt confirmation,
before dow. Exact one-key dictionary and zero register value required; register
error/malformed/nonzero response stops before download. Markers identify stop,
halt, register-read, download-start/completion and resume-completion. Existing
final bootstrap marker still does not replace full normal restoration tests.
No retry, forced access, alternate address mode, private AP0 or AIB write added.

Installed XSDB2025.2 source supports -nvlist: rrd options at line3452 onwards,
name/value dictionary assembly at2789 onwards; another installed command uses
rrd -nvlist pc. Source hash recorded. r0 hardware response schema still requires
physical qualification; no device opened to inspect it in this turn. This gate
cannot guarantee subsequent RAM write success or eliminate a time-of-check race.

Four real-Tcl mock tests PASS: ordered bootstrap, unconfirmed halt/no download,
register error/nonzero/no download, and download error/no resume/no final marker.
Six parent lifecycle tests PASS. Model backends do not prove physical recovery.
New helper hash deliberately invalidates old deployment manifests; preserve old
pins as historical. No new physical trial admitted with stale manifests.

Next offline update a fresh recovery/candidate plan with exact changed helper
pins and explicit no-retry failure handling. Current normal baseline remains
usable192.168.2.3 as recovered earlier; no new health check or guard attempt.
Full DDR NOT_ADMITTED. No Si/SD/flash/OTP/Kasli changes.
