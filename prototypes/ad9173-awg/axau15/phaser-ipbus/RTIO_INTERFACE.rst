Phaser envelope / DRTIO integration contract v1
=============================================

This side supplies the generator endpoint. The neighbouring DRTIO project
supplies the satellite, RTIO scheduler/SED, routing, recovered clock and
timeline-valid/reset signals. No DRTIO link, FPGA programming or Kasli
access is performed by this integration preparation.

Stage one is deliberately small: IPbus uploads DDS parameters and the
finite envelope program, ARM validates and reserves it, and one scheduled
RTIO START consumes that reservation. Completion holds zero. Frequency,
amplitude and phase changes remain IPbus operations before ARM. DDS phase
continues through ARM/START and zero envelopes; there is no rephase-on-START.

IPbus ownership
---------------

ARM-capable images report ABI0x00010002 and capabilities0x008=3. Earlier
qualified envelope images use ABI0x00010001/capabilities1; old CW uses
ABI0x00010000. The host client accepts all three for DDS operations and
rejects ARM on either older image.

Additional word-addressed registers::

  025 write3: ARM (write1 immediate START and write2 BYPASS still available)
  027 read: armed, synchronized registered JESD status
  028 read:30-bit ARM ID, valid/stable after armed becomes1

``EnvelopePhaser.arm(repeats)`` returns this ID after validation and first
entry prefetch. Busy0x020 stays1 throughout ARM, playback and pipeline
drain. RAM writes, length/repeat writes, new envelope commands and DDS COMMIT
are rejected until completion or ABORT. DDS shadow staging remains possible;
it cannot change active parameters. Global FPGA mute and IPbus ABORT remain
available. Invalid programs never become armed.

Keep the shared ALINX hardware lease across upload, ARM, the ARTIQ experiment,
completion and restoration. The Python API does not acquire it itself.
Do not release an armed board for an unrelated thread to reprogram.

RTLink ABI
----------

``EnvelopeRTIO(player, rtlink)`` and ``EnvelopeRTIOBridge(player, rtlink)``
use the integrator's actual ``artiq.gateware.rtio.rtlink`` module. Output
width32, no address or fine timestamp, ``enable_replace=False``. Input
width8, NOT timestamped. Add the selected PHY through the normal
``Channel.from_phy(phy)`` path in the satellite.

Output data::

  bits1:0 =0 QUERY,1 START,2 ABORT,3 invalid
  bits31:2 = ARM ID for START; ignored for QUERY/ABORT

A START only succeeds while armed and with a matching ID. Each ARM attempt
increments the30-bit ID, including invalid programs; it survives JESD-domain
runtime reset and wraps modulo2^30. Do not retain commands across FPGA
reprogramming or2^30 ARM attempts. An early, stale, duplicate or late START
is rejected, never saved for a later ARM. ABORT is intentionally untagged
and forces envelope-zero mode, including from continuous-wave bypass.

Input response::

  bits3:0 =0 accepted,1 bad command,2 not ready/armed,3 stale ARM ID,
           4 timeline disabled/reset
  bit4 = armed before command, bit5 = playing before command
  bits7:6 =0

The response acknowledges command admission, not pulse completion. Observe
IPbus busy/result for completion. The integration must consume these input
responses; otherwise the RTIO input FIFO can overflow. ``artiq_envelope.py``
provides kernel START/ABORT/QUERY methods and blocking ``read_response()``
(raw byte) / ``check_response()`` (raise ValueError on rejection). Consume
exactly one response per admitted command, in FIFO order; do not mix these
readers with another consumer on the same channel. Accepted responses retain
bits4/5 describing the state before the command, not its completion.

These readers use upstream ``rtio_input_data`` and have no timeout. A command
dropped due to busy, timeline reset or link loss may never produce a response;
do not blindly read after a known failed output. Recovery belongs to the
satellite/runtime and must invalidate outstanding command/response pairing.
Responses do not carry a command ID. After uncertain recovery, establish an
empty input FIFO and a new ARM before resuming; never retry START implicitly.

For a single command after a fresh ARM and with a ready bridge::

  awg.start(arm_id)       # at the timestamp selected by the experiment
  awg.check_response()   # admission only; may consume timeline slack
  core.break_realtime()  # before scheduling a subsequent output

Do not insert a blocking read into an uninterrupted timed output sequence.
The host-semantics regression uses the real ARTIQ decorators with mocked
RTIO syscalls. It checks encoding, token limits, ordered reads, all rejection
codes, reserved/unknown values and propagation of transport exceptions::

  /srv/codex-hil-data/artiq-zynqmp/venvs/artiq-host/bin/python \
    -m unittest -v test_artiq_envelope_host

Five host tests PASS. This is not NAC3 compilation or kernel execution on a
core; those remain pending with the satellite integration.

Clock choices and reset
-----------------------

``EnvelopeRTIO`` is synchronous in ``jesd``. Use it directly only when the
scheduler's output events are synchronous to that exact clock; frequency
similarity is insufficient. The strobe sampling edge installs the first
prefetched gain. ``EnvelopeStage`` adds six JESD clocks after that edge.
This does not include JESD transport, DAC interpolation or analog latency.

For the current independent clocks, ``EnvelopeRTIOBridge`` accepts events in
``rio_phy`` and forwards them to ``jesd`` using a one-event held-data mailbox.
It asserts RTLink busy while disconnected or while an event/response remains
outstanding. An event presented while busy is dropped by the normal RTIO
busy-error mechanism; the bridge does not queue or automatically retry it.
Avoid status queries near scheduled START events. Local envelope repeats do
not require additional RTIO transactions.

The asynchronous bridge adds variable crossing latency and quantization to
the JESD clock. It does NOT make RF start deterministic relative to Kasli's
TSC. Shared reference/phase alignment or a timestamp-aware destination
scheduler is still needed before making that claim.

Connect ``enable`` to a registered source-domain timeline-valid condition,
not merely optical link-up; connect ``reset`` to the RTIO experiment reset.
The bridge also observes ``ResetSignal('rio_phy')``. Deasserting enable or
resetting the source cancels playback after crossing latency, keeps outputs
zero while offline, drains outstanding requests and requires a full offline/
online handshake before admitting another event. Short source reset pulses
are held by this handshake until JESD observes the offline state. Source
reset must be sampled by rio_phy. If JESD stops, cancellation cannot advance
until that clock resumes; there is no analog mute guarantee with a lost clock.

The net and JESD resets are board-level resets, not independently qualified
hot-reset interfaces. Disable the timeline, cancel and wait idle before
resetting net/IPbus, or perform a coordinated reset then reload and ARM.
Do not independently reset the net-domain ownership registers during ARM.
After JESD clock loss/reset, invalidate the timeline and reinitialize/rearm;
physical clock-loss recovery remains unqualified.

Suggested connection (names on the DRTIO side are placeholders)::

  from artiq.gateware.rtio import rtlink, Channel
  self.submodules.awg_rtio = awg_rtio = EnvelopeRTIOBridge(player, rtlink)
  self.comb += [awg_rtio.enable.eq(timeline_valid),
                awg_rtio.reset.eq(experiment_reset)]
  rtio_channels.append(Channel.from_phy(awg_rtio))

Keep existing IPbus Registers/EnvelopePlayer/EnvelopeStage wiring. Both
``rio_phy`` and ``jesd`` domains must exist. Adapt constraints to the actual
hierarchy and clock rates; do not add blanket asynchronous clock false paths.

Validation and handoff
----------------------

``test_rtio.py`` uses upstream RTLink types and checks prevalidation/ownership,
one-cycle steps across repeats, exact local pipeline latency, stale-token
rejection, cancellation, source-only reset/reconnect and50 consecutive
mailbox responses without duplication or loss. Existing DDS/FIFO/envelope
regressions remain applicable. No new hardware validation is claimed.

``prepare_rtio.py FRESH_DIRECTORY`` generates an out-of-context integration
of actual DDS, envelope multipliers, registers and asynchronous RTLink bridge
for xcau15p-ffvb676-2-i. Build only on Dell with the shared Vivado lease.
It has no GTH/pinout or bitstream. Timing model:net/rio_phy125MHz,
JESD153.6MHz; synchronous boundary input delays0.2..1ns, output0..1ns.
The input hold budget is a parent-interface requirement, not a measured PCB
number. Parent-level clock/reset distribution, pin/GT integration and timing
closure must be checked again. Held buses and first synchronizer stages have
6ns datapath bounds; held buses additionally have6ns skew bounds.

Standalone board builds use ABI0x00010002 but have no scheduled RTIO source
until one of these endpoints is connected. Their qualification runner needs
``--profile armed`` for the extra stable ARM-ID CDC status bus. Existing
ABI0x00010001 artifact/evidence remains immutable and physically qualified.
The shared default SRAM image remains the original CW149/151MHz image.

2026-10-24 result:23 RTL tests PASS (eight new RTIO cases), UDP regression
PASS, ARTIQ host import/command encoding PASS. Final OOC implementation PASS:
WNS+2.893ns,WHS+0.037ns, no critical CDC or DRC errors, four skew groups PASS.
Regenerated inputs are byte-identical. Evidence:
``../../evidence/axau15/rtio-interface-20261024/acceptance.json``.
No FPGA/DRTIO/Kasli/RF access occurred in this stage. The full satellite,
NAC3/runtime execution and physical timestamp-to-RF timing remain NOT_RUN.
