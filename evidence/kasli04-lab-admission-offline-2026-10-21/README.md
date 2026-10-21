# Lab-only backend admission callback telemetry (offline)

Normal firmware.c, ddma_backend.h and ddma_runtime.h unchanged. Generated
laboratory C includes a wrapper around the original backend, forwarding
exactly the same callbacks/arguments/results and propagating its fault latch.
The wrapper adds no MMIO/time reads and emits UART only after rejection.
It records last step, ready/time call counts/results, last sampled now,
requested timestamp and last address/value. Step1=ready,2=time,3=MMIOread,
4=MMIOwrite,5=copy,6=flush,7=delay; step0 is intrinsic input rejection.
This allows interpreting which original short-circuit admission check failed.
Instrumentation has CPU overhead; it is not timing-neutral or independent
clock measurement. No UART output is added to accepted start.

Differential native C test PASS for8cases: success, early/late margin, active,
pending,timeout,missing callback,invalid size. Original and wrapped result,
fault latch and mock I/O state/callback counts match.3map/overlay,4admission
and3sessiontestsPASS. Rebuilt A53 ELF PASS; hashes in results.json. Old lab
images are refused by current admission due new overlay/header hashes.
Normal KASLI04 pinned profile offline preflight remainsPASS.

No hardware access this checkpoint. New ELF requires new physical lab-idle
qualification before active mode; old idle proof is not reusable for this
changed ELF. Next run idle/DIO/snapshot/counter/restoration, then admit one
active test with the new exact proof. No lowered margins or bypassed checks.
