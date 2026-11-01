# Separate Genesys cold-recovery window

SPDX-License-Identifier: LGPL-3.0-or-later

Status: reviewed procedure; NOT_EXECUTED. Existing authorization covers control
of the devkit-only plug. No new PMU candidate or exception policy is admitted.

1. Re-identify Optiplex, exact Genesys cable 210383B7F02DA and stable UART
   by-id; acquire shared Genesys flock nonblocking and unique plug reservation.
   Hold both throughout observation, switching and restoration. Busy means stop
   device access and do independent offline work. Keep plug token private.
2. Verify baseline manifest and actual restore reserves on all affected filesystems.
   Identify live server/UART/interface under lease; do not reuse stale addresses.
   Record normal runtime identity before changing it if available.
3. Establish an independent board-power observation before OFF: a documented
   supply/power-good or POR indication with a known interpretation and an observer
   independent of the switched devkit. No such source has been established by the
   current evidence. Relay report, old power fields, USB enumeration, ping loss
   and UART silence alone cannot certify de-energization or POR. Camera LED views
   may support a limited observation but are not calibrated supply measurements.
4. With independent control infrastructure and observer available, issue one
   explicit OFF through hil-plug; separately read status and record the board
   observation. No TOGGLE, automatic cycle, shell sleep/on timer or watchdog.
   Before switching, retain a usable independent ON control path. If OFF outcome
   is uncertain, do not retry OFF or proceed to firmware experimentation.
5. Perform ON as a separate explicit operation through the same reservation.
   Record reported state and independent board startup/POR evidence. Missing
   evidence leaves cold recovery UNKNOWN even if subsequent JTAG boot succeeds.
6. Only after exact target identity returns, restore normal images via existing
   baseline boot/load tools. The JTAG qualifier begins with PMU halt/register
   access/download and assumes PMU target availability; do not use it as proof
   that an unavailable target can be recovered. No alternate memory alias/forced
   access or retry cascade. No flash/OTP/SD/Si/other board writes.
7. Verify normal UART identity/DHCP, TTL/CoreDMA/debug and Ethernet. Record each
   failed stage literally; release claims after a known final state. If control
   fails after switching, report the final known state and required operator
   action; preserve an unreleased plug token privately when release fails.

The next executable preparation remains bounded read-only live target/runtime
identification under shared claims. Before a cold window, independently qualify
its observation source. If it requires wiring or a physical measurement, stop
there for the operator rather than inferring a voltage/POR state from software.
