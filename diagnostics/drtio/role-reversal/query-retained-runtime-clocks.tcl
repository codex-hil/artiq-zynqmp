# SPDX-License-Identifier: LGPL-3.0-or-later
# In-memory diagnostic case analysis only, never save or deploy these assumptions.
set_param general.maxThreads 4
open_checkpoint /srv/nvme-fast-1/vivado-work/genesys-retained-local-cdc-20261112-v1/combined_cdc.dcp
report_clocks -file baseline-clocks.rpt
source query-gt-clock-parameters.tcl
source query-runtime-gt-clocks.tcl
source query-rxrate-runtime.tcl

close_design
puts "RETAINED_RUNTIME_CLOCK_DIAGNOSTIC_COMPLETE"
