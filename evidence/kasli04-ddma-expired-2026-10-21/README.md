# KASLI04 native DMA expired-start rejection/recovery PASS

One valid170-byte trace uploaded. Start timestamp8 rejected by native AUX
playback admission; standard kernel caught DMAError. Same kernel then
played the same uploaded trace at a future timestamp without reset/reupload:
physical8edges,width8000mu,period80000mu,firstdelta1000120mu. Exact upload
ACK/startNACK/futureplayACK/status0/eraseACK sequence and trace ID passed.
No kernel/session abort, new native service fault or checked RTIO error.

This is expired admission rejection, not active hardware playback underflow.
Sorted04+Genesys leases held through test/restoration.04clock/originalmux71/
mode10 and Genesys localCoreDMA/debug/Ethernet192.168.2.3 restorationPASS,
leasesreleased. No01/03/Flash/OTP/SD/GenesysSi writes. Next same-kernel
malformed upload rejection/cleanup/recovery, then separately gated fault lab.
