# Directed AIB mapping and baseline ownership — 2026-10-27

Offline decode of retained physical words REQ/ACK00c00000,TYPE19cf000f.
Exact header crosscheck for REQ/TYPE/ACK14AXI instances PASS; bits22/23 are
USB0S/USB1S, instances7/8: LPD master-side interconnect to USB slave interfaces.
They do NOT isolate USB DMA masters from DDR or establish a complete DDR drain.
RPUM0/1 bits16/17 and RPU-via-LPD-to-DDR bit27 are clear. Unknown/reserved bits
reported separately, TYPE raw bits retained without assigning response semantics.

Two mapping tests PASS including direction, changed header, unknown high bit and
malformed integer controls. Five ACK model tests PASS: actual observed USB
baseline bits are preserved in proposed RPU-only request0x00c30000; any loss of
those unrelated bits is hard failure. Synthetic model only, not actual isolation.

Candidate pm_usb.c associates USB0/1 with these AIB IDs. ON->OFF/UNUSED enables
AIB then calls powerdown; OFF/UNUSED->ON calls powerup, disables AIB then pulses
reset on success. This supplies a plausible source path, not proof of which code
established captured bits. Searched candidate app/PS initialization sources did
not identify a unique literal initializer for retained REQ/TYPE; boot ROM, runtime
PM transitions or earlier state remain possible. No initializer attribution claim.

UG1085v2.5p1162 special RPU reset explicitly allows timeout then continuation.
Thus previous void-helper timeout behavior is not called a general vendor bug:
it is unsuitable as a strict diagnostic completion receipt. p420Table16-17
provides direction mapping. Official source previously inspected:
https://docs.amd.com/api/khub/documents/xzMsp_c5sG9J6A3u7NkJYQ/content?Ft-Calling-App=ft

Next offline: isolated C implementation of strict RPU-master-only ACK/hold with
mocked register backend, preservation of observed USB bits, finite deadline and
failure-hold behavior. No live AIB write approved by this map. Must still review
control/debug/OCM access, source halt and internal PMU/ROM writers before a
physical candidate. No HW access or runtime changes; DDR NOT_ADMITTED.
