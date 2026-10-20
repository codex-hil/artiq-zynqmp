# KASLI01 master FPGA qualification

Vivado 2025.2 implementation and bitstream generation passed. Setup slack
0.092 ns, hold slack 0.051 ns, pulse-width slack 0.264 ns; zero failing
endpoints in the timing summary. The qualifier checks the exact source
overlay, part, reset-zero ROM wiring, bootloader initialization and hashes.
Inherited external timing warnings remain a limitation; timing closure alone
does not establish physical operation or deterministic DRTIO latency.

Source/CPU evidence: `../kasli01-master-source-2026-10-20` and
`../kasli01-master-cpu-2026-10-20`. Large bit/bin artifacts remain under
the build path recorded in qualification.json. No flash image is installed.
