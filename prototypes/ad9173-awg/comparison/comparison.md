# RF A/B comparison — NOT_RUN

> Scope correction, 2026-10-23: the user confirmed the NEW devkit is AD9172.
> First priority is basic devkit bringup; DRTIO/Phaser comparison is deferred.
> AD9173 rates, register IDs and physical PASS below describe the preserved
> Trenz reference only, not qualification of the new AD9172. No target rate
> (including 12.6 GS/s) has been configured or verified.


No spectrum traces or comparison numbers have been acquired. Historical Trenz
oscilloscope fits are not baseline A or target B spectrum measurements.

## Frozen scope

Existing AD9173 RevC backend, stock Phaser baseline. First compare150 MHz CW,
then simultaneous150/151 MHz on the same RF output, equal per-tone amplitude.
Historical149/151 MHz on separate DACs is not this IMD test. Follow with controlled
amplitude/frequency changes and multiple reinitializations. Four-tone mode,
MIQRO/AWG/envelope/DPD extensions are excluded.

Use one common experiment with documented backend adapters and identical SI
parameters. Identify RF output/sideband and frequency plan explicitly. DDS
frequency, DAC NCO and any Phaser DUC/upconverter contributions must be recorded.
Begin two-tone operation with headroom (sum of oscillator amplitudes below full
scale, including interpolation transient margin); match measured analyzer input
levels rather than assuming equal digital amplitudes produce equal power.

## Measurement record required before PASS

Each measurement JSON/CSV must include: run ID/time; A/B device serial and output;
experiment commit; bitstream SHA256; ARTIQ/driver versions; DAC/DRTIO/JESD status;
frequency/amplitude/phase commands; reference clock and locking state; analyzer
IDN/firmware/calibration date; path/attenuator calibration and uncertainty;
center/span/RBW/VBW/detector/averaging/input attenuation/preamp/reference level;
raw SCPI command log; trace units/frequency bins and file hashes; environmental
conditions; marker frequencies/powers and fit/estimation method; harmonics,
spurs/noise floor and stated SFDR bandwidth; uncertainty and compression checks.

Keep analyzer settings identical for A/B. Connect sequentially through the same
calibrated path or characterized RF switch; never directly combine live outputs.
Use common10 MHz where supported, and document devices that cannot accept it.
Verify compression by a known extra input attenuation step and appropriate level
correction before attributing IMD to either source. Do not issue model-specific
SCPI configuration until analyzer identity and ratings are known.

For150/151 MHz tones, look for IM3 at149/152 MHz and IM5 at148/153 MHz; overlapping
spurs, analyzer nonlinearity and noise limits must be distinguished. Report
non-detection as an upper bound tied to RBW/noise, not zero distortion. Power
and relative amplitude include cable/switch/attenuator uncertainty. Scalar
spectra do not prove phase coherence; use common-reference phase-capable capture
for phase/reset assertions and a separate RTIO timing test.

Reuse `/home/codex-hil/lab-instruments` (`python3 -m labinstruments`) after model
commissioning rather than introducing another service. Inspected local commit:
`c0ddc6b4f6b8a0176abd6abae8fb91b1dd4edb88`. No guessed analyzer address, device
model, programming command or simulated trace is presented as measured evidence.

## Acceptance table

| Stage | State | Missing evidence |
|---|---|---|
| M0 inventory | PARTIAL | physical board/adapter/clock and baseline identification |
| M1 satellite | BLOCKED | usable DRTIO PHY/refclock, board lease, stock master details |
| M2 local DDS | NOT_RUN | M1 pass, rate/command semantics verified in vectors |
| M3 JESD integration | NOT_RUN | M1/M2, cold init and ALINX physical links/sample proof |
| M4 A/B RF | NOT_RUN | calibrated analyzer/path and both controlled RF sources |
| M5 repeatability | NOT_RUN | repeated M4 across documented cold/link restart runs |
