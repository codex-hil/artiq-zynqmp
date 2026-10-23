AXAU15 / AD9172 VADJ review — 2026-10-23
======================================

Result: DOCUMENTARY_COMPATIBILITY_AT_1V8; PHYSICAL_VADJ_NOT_MEASURED.
User reports AXAU15 connected to Optiplex by USB and Ethernet, without DAC.
No programming, rail changes, EEPROM writes or device SPI access performed.

AXAU15 supplied 44-page manual, sections3.4 and3.12 (pages29,42–43):
FMC GPIO uses BANK64/65 at1.8V. Separate U175 ETA1471 supplies VADJ/3A;
text says a jumper can select1.2V. This does NOT establish the current jumper
position or actual VADJ. No reliable jumper designator/position table appears
in those sections. Do not infer VADJ from FPGA IO voltage or set it through
an invented software register. Manual hash/path is in axau15-manual-pinmap.json.

Local AD9172_FMC_EBZ schematic /home/codex-hil/trenz-bringup/reference/dac.pdf,
drawing02_046765 revisionD, sheet7: U7/U13 FXL4TD245BQX have VCCA=VADJ,
VCCB=LT3V3. They translate carrier SPI/GPIO; DAC-side1.8V is separately
translated by U9/U10. Sheet8 brings VADJ from FMC. Sheet6 ADP1763 pins named
VADJ are regulator adjustment pins, NOT the FMC VADJ supply net.
The exact revision of the newly supplied AD9172 board remains to be confirmed.

FXL4TD245 recommended VCCA/VCCB range is1.1–3.6V;1.8V is supported.
Source: https://www.onsemi.com/pdf/datasheet/fxl4td245-d.pdf page3.
Thus the documented carrier1.8V GPIO and mezzanine translation are compatible
at VADJ1.8V. Translator support for1.2V does not establish reliable1.8V-FPGA
input thresholds when receiving1.2V signals. Do not select1.2V for this target
without a separate full IO analysis. Similarly, the translator's3.3V support
is not permission to drive carrier1.8V banks with3.3V signals.

Before mating the DAC, confirm actual carrier revision/jumper and measure
VADJ relative to GND at an identified accessible test point with FMC empty.
Target nominal1.8V. A photograph of the VADJ jumper markings/full carrier and
matching schematic is needed to specify the exact test point/position safely;
do not guess a fine-pitch connector contact or jumper number. Power off before
changing jumpers or mating FMC. This check covers VADJ only:12V power budget,
clock levels/population and SYNC/SYSREF electrical compatibility remain separate.

Public supporting sources:
https://www.alinx.com/public/upload/file/AXAU15_UG.pdf (older manual revision)
https://wiki.analog.com/resources/eval/dpg/eval-ad9172 (ADI design files index)
