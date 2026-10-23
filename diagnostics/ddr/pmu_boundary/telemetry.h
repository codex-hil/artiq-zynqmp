/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef ARTIQ_PMU_BOUNDARY_TELEMETRY_H
#define ARTIQ_PMU_BOUNDARY_TELEMETRY_H
#include <stdint.h>
/* PMU-local BSS only. No transport/host address assigned; NOT a quiescence ACK. */
struct artiq_pmu_boundary_record {
 uint32_t sequence, magic, version, loop_count;
 uint32_t ack, unresolved, reserved0, reserved1;
};
static volatile struct artiq_pmu_boundary_record artiq_pmu_boundary;
static inline void artiq_pmu_observe_boundary(void) {
 artiq_pmu_boundary.sequence++;
 artiq_pmu_boundary.magic=UINT32_C(0x504d5542);
 artiq_pmu_boundary.version=1;
 artiq_pmu_boundary.loop_count++;
 artiq_pmu_boundary.ack=0; /* Unconditionally observation-only. */
 artiq_pmu_boundary.unresolved=UINT32_C(0x7f); /* All seven obligations unproven. */
 artiq_pmu_boundary.reserved0=0;
 artiq_pmu_boundary.reserved1=0;
 artiq_pmu_boundary.sequence++;
}
#endif
