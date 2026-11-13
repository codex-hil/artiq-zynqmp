# SPDX-License-Identifier: LGPL-3.0-or-later
# Diagnostic comparison only; no saved checkpoint or CDC/timing waivers.
set_param general.maxThreads 4
open_checkpoint /srv/nvme-fast-1/vivado-work/genesys-retained-local-cdc-20261112-v1/combined_cdc.dcp
report_cdc -details -file baseline-cdc.rpt
report_clock_interaction -file baseline-interaction.rpt
source query-runtime-gt-clocks.tcl
source query-rxrate-runtime.tcl
report_cdc -details -file steady-cdc.rpt
report_clock_interaction -file steady-interaction.rpt
report_exceptions -file exceptions.rpt
close_design
puts "STEADY_CDC_COMPARISON_COMPLETE"
