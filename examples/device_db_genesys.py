# Genesys local-RTIO variant. Update host to the actual DHCP address.
# Management works; network kernel execution is not integrated yet.
device_db = {
    "core": {
        "type": "local",
        "module": "artiq.coredevice.core",
        "class": "Core",
        "arguments": {"host": "192.168.2.16", "ref_period": 8e-9,
                      "ref_multiplier": 1, "target": "cortexa9"},
    },
    "ttl": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 0},
    },
}
