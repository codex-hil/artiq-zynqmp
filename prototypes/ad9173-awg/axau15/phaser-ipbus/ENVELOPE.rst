Finite complex envelopes over IPbus
==================================

The AXAU15 Phaser target adds a local, finite sequencer after the two
five-tone DDS generators. It applies one complex Q1.15 gain per output,
shared by the two samples generated in each 153.6MHz JESD clock cycle.
The DDS still runs at307.2MS/s and the DAC at4.9152GS/s. This sequencer is
not upstream MIQRO, an ARTIQ driver, DRTIO or timestamped RTIO.

A program holds1..256 entries. Each entry specifies a duration of1..2^32-1
JESD cycles and independent complex gains for DAC0 and DAC1. Programs can
repeat1..2^32-1 times without gaps. Minimum step duration is6.5104167ns
nominal. Ethernet determines when the command arrives; it does not provide
a deterministic trigger time. The whole program is checked for zero
length entries before playback; invalid programs emit no partial pulse.

Default after FPGA configuration is continuous DDS bypass. START selects
envelope mode, prevalidates the program and starts playback. Completion
or ABORT leaves both envelope gains at zero. BYPASS explicitly returns to
continuous DDS. ABORT in bypass mode does not mute continuous RF; use the
existing global mute register for that. The sequencer never resets DDS
phase: oscillator phase continues during zero-envelope intervals.

The gain stage uses four pipelined complex multipliers, rounding and
signed16-bit saturation. Bypass and envelope paths both add exactly six
JESD cycles; acknowledgements wait for the pipeline to drain. This digital
latency is not a measurement of deterministic end-to-end DAC/RF latency.
The host accepts gains within the complex unit circle. Raw register
writes can exceed it, in which case the output saturates. Positive unity
is represented by32767/32768, negative unity by-1.

Register ABI
------------

Envelope images report ABI0x00010001 and capabilities register0x008=1.
The previous CW image reports ABI0x00010000. The existing DDS client accepts
both; the envelope client checks the new ABI before accessing these words.
Addresses are32-bit word addresses, not byte addresses::

  020 RO busy: request or abort outstanding, including validation/drain
  021 RO bit0 envelope mode, bit1 playing, bits5:4 result
         result0 OK,1 aborted,2 invalid; result is final only when !busy
  022 RO completed command count (wraps at32bits)
  023 RW program length1..256, idle only
  024 RW repeat count1..0xffffffff, idle only
  025 WO command1 START,2 BYPASS; rejected while envelope or DDS busy
  026 WO write1 ABORT; rejected while another abort is pending
  400..7ff RW program RAM:256 entries, four words per entry

Entry words::

  +0 duration in153.6MHz clocks, must be nonzero
  +1 DAC0 gain: signed I in bits15:0, signed Q in bits31:16
  +2 DAC1 gain: same encoding
  +3 reserved: reads0, only write0 accepted

RAM and command fields cannot be changed from request until completion,
including while the JESD clock has stopped. DDS COMMIT is also rejected
while envelope busy. Shadow DDS words can be staged; they have no effect
until a later valid commit. Global mute remains available during playback.
The program RAM uses separate synchronous net/JESD ports. A held43-bit
command bank, synchronized request/ack toggles and6ns datapath/bus-skew
constraints protect configuration transfer. The RAM ownership protocol
prevents simultaneous host writes and playback reads. The command capture
uses a dedicated DIRECT_ENABLE net so synthesis retains an identifiable CE
on every destination bit; see AMD UG912:
https://docs.amd.com/r/en-US/ug912-vivado-properties/DIRECT_ENABLE .
A START cancelled before the JESD clock resumes also enters zero mode.

Host usage
----------

All hardware access requires the shared ALINX lease documented in
``../../BOARD_SHARING_ALINX.txt``. ``envelope_client.py`` CLI takes it for
the whole finite run; direct ``EnvelopePhaser`` API callers must take it.
The command has no automatic write/START retry. On a timeout or uncertain
START response, the CLI attempts ABORT before releasing its lease.

Example JSON format: each entry is[cycles,[I0,Q0],[I1,Q1]]::

  [[16,[0,0],[0,0]], [16,[0.5,0],[0.5,0]],
   [16,[0,0],[0,0]], [16,[1,0],[0,1]]]

On an initialized envelope image::

  python3 envelope_client.py --play example-envelope.json --repeats 1000
  python3 envelope_client.py --status
  python3 envelope_client.py --bypass

Playback does not automatically unmute the existing global DDS mute.
The CLI leaves envelope mode at zero after completion; BYPASS re-enables
continuous DDS. It records its last observation in the shared state file.

``run_envelope.py BIT --sha256 HASH --output FRESH_DIRECTORY`` performs
bounded physical qualification. Timing/CDC/DRC/skew reports must accompany
the bitstream; the runner checks them before obtaining hardware leases.
Use the vector-analyser Python environment
for NumPy/SciPy. It acquires scope then ALINX, verifies the prior CW ABI,
programs SRAM, performs warm DAC/JESD startup, and measures only CH3/4.
It restores the shared golden CW image and149/151MHz under the same lease,
including after a test failure, and records restoration separately.
No HMC reset, persistent memory write or global scope setting change occurs.
Cold-start clock initialization remains a separate task.

Validation
----------

Current qualification:15 RTL tests, localhost UDP regression and two synthetic
RF analysis tests PASS. Vivado2025.2 implementation PASS:WNS+0.148ns,
WHS+0.011ns, no critical CDC or DRC errors, all six bus-skew groups PASS.
Physical qualification PASS on MSO4104 CH3/4:0/half/full levels, independent
channel amplitudes, alternating90-degree complex gains, and a64-step Gaussian.
Measured Gaussian shape RMSE is1.61%/1.55% of full-scale amplitude. Adjacent
pulse phase steps are within0.27degrees of90degrees in these captures; this
is not a calibrated absolute phase or inter-channel synchronization claim.
Full256-entry RAM readback,32-bit repeats/abort, natural finite completion,
invalid-duration rejection, held zero and explicit CW bypass also PASS.

The runner restored the shared ABI0x00010000 image under the same lease:
CH3=148.995869MHz/0.47558Vpp,CH4=150.995986MHz/0.48292Vpp, JESD0x1ff.
Scope settings were restored and read back. Raw captures, program logs and
separate simulation/implementation/acceptance records are retained.

Candidate bitstream:
``/srv/codex-hil-data/artiq-zynqmp/artifacts/alinx-envelope-20261024f/phaser_ipbus.bit``

SHA256::

  2ebe2318b661438e8d509ac26a9de51c2f1959fe15692da39f59ac428b0fcd3a

Simulation, Vivado implementation and physical RF evidence are recorded
separately in ``../../evidence/axau15/envelope-20261024``. The existing shared
CW image remains the default handoff artifact; envelope tests restore it.
