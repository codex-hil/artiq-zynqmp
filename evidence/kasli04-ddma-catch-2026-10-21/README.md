# KASLI04 native DMA rejected-upload catch and recovery PASS

Malformed fragmented upload rejected before playback; kernel caught DMAError.
Native rejected trace cleanup acknowledged, same-name valid170-byte trace
uploaded and played in the same kernel without intervening reset/restart.
Physical8edges,width8000mu,period80000mu,firstdelta1000120mu. Exact AUX negative/
positive fragment lengths, NACK, cleanup ID and successful play/status/erase
sequence validated; no new kernel/session abort or service fault.

Both-board restoration PASS under sorted04+Genesys leases:04clock/original
mux71/mode10,Genesys localCoreDMA/debug/Ethernet192.168.2.3;leases released.
No01/03/Flash/OTP/SD/GenesysSi writes. This is upload validation/recovery,
not active hardware underflow. Next verify timeline cursor restoration on
both success and exception using the previously reviewed isolated host overlay.
