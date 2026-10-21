# KASLI04 DMA timeline cursor success/exception restoration PASS

Used the existing hash-validated isolated host DMA cursor overlay. Standard
kernel checked exact saved now_mu after successful record and after rejected
upload/DMAError, before break_realtime resynchronization. Both checks PASS,
then same-kernel physical playback8edges PASS. Rejected trace cleanup and
normal AUX upload/play/status/erase validated; no new master/service fault.
Default host installation unchanged. Not active hardware underflow proof.

Sorted04+Genesys leases held through full session and restoration.04clock/
originalmux71/mode10 and Genesys localCoreDMA/debug/Ethernet192.168.2.3
restorationPASS; leasesreleased. No01/03/Flash/OTP/SD/GenesysSi writes.
Next physically qualify idle lab firmware/independent counters before any
active-delay injection; do not reuse normal idle proof for that lab gate.
