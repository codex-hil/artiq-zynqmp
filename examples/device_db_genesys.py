# Genesys local-RTIO variant. Update host to the actual DHCP address.
# Network kernels/RPC and local RTIO bindings work; physical loopback pending.
device_db = {
    "core_dma": {
        "type": "local", "module": "artiq.coredevice.dma", "class": "CoreDMA",
    },
    "core": {
        "type": "local",
        "module": "artiq.coredevice.core",
        "class": "Core",
        "arguments": {"host": "192.168.2.16", "ref_period": 8e-9,
                      "ref_multiplier": 1, "target": "cortexa9"},
    },
    # Fixed input PHY: use gating/counting, do not call input()/output().
    "ttl_in": {
        "type": "local", "module": "artiq.coredevice.ttl", "class": "TTLInOut",
        "arguments": {"channel": 1},
    },
    "ttl": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 0},
    },
}
