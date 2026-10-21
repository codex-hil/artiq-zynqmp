# KASLI04 qualified FPGA and physical boot; netboot timeout

Vivado implementation/ROM/hash qualification PASS; setup/hold/pulse margins
0.092/0.051/0.264ns. Per-board MAC02:4b:04:70:48:54, no-EEMmux source overlay.
Physical DNA/retained-mode10 precheck and SRAM boot PASS. Bootloader CRC,
SDRAM initialization and inherited memory test PASS. The first IPv6 netboot
TCP connection timed out; no runtime payload or boot command sent. Runtime,
management and external DRTIO therefore NOT_RUN. This does not establish the
physical cause of the missing network connection.

Temporary diagnostic restoration and final retained mode10 restoration PASS.
Clock configuration untouched. Both04/Genesys leases released, Genesys not
accessed, no other Kasli/flash/OTP/SD writes. Need confirm KASLI04 SFP0 network
connection to the host/switch; SFP1 is reserved for user-confirmed Genesys
DRTIO connection. No repeated identical trial until host network path checked.
