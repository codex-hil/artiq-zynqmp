# Genesys user-authorized Zigbee ON — 2026-10-30

Owner confirmed plug supplies only the Genesys devkit and left it OFF, explicitly
authorizing ON. Optiplex hostname verified; shared Genesys flock and unique plug
reservation held through ON/status. CLI verified plug identity; MQTT delivery
and subsequent non-retained device publication report ON. No OFF/cycle, debug,
UART/network test, FPGA/firmware write or policy change. Plug reservation and
board flock released; reservation token not retained in Git.

Reported power/current0 and voltage234 have unknown field freshness and do not
prove no load or successful devkit start. Physical outlet voltage, actual POR,
board boot and normal runtime remain unverified. This establishes owner mapping
and reported ON command outcome, not an autonomous recovery/watchdog guarantee.
