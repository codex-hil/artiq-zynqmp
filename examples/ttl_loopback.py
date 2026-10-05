"""ARTIQ 9 acceptance experiment, pending a real kernel/runtime backend.

Requires validated device_db, JB1 -> JB2 and the local-rtio variant.
The current prototype daemon rejects this kernel; it cannot execute it.
"""
from artiq.experiment import EnvExperiment, kernel, parallel, sequential, delay, ms, us


class TTLLoopback(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl_out")
        self.setattr_device("ttl_in")

    @kernel
    def run(self):
        self.core.reset()
        self.ttl_out.off()
        self.ttl_in.input()
        self.core.break_realtime()
        with parallel:
            end = self.ttl_in.gate_rising(1 * ms)
            with sequential:
                delay(100 * us)
                self.ttl_out.pulse(10 * us)
        count = self.ttl_in.count(end)
        if count != 1:
            raise ValueError("Expected exactly one TTL rising edge")
