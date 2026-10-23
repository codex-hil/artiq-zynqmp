/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef ARTIQ_PMU_BOUNDARY_REQUEST_H
#define ARTIQ_PMU_BOUNDARY_REQUEST_H
#include <stdint.h>
struct artiq_pmu_request_record {
 uint32_t generation, nonce_lo, nonce_hi, sequence_lo, sequence_hi, kind, checksum, reserved;
};
struct artiq_pmu_echo_record {
 uint32_t generation, nonce_lo, nonce_hi, sequence_lo, sequence_hi, status, ack, reserved;
};
static volatile struct artiq_pmu_request_record artiq_pmu_request;
static volatile struct artiq_pmu_echo_record artiq_pmu_echo;
static uint64_t artiq_pmu_last_sequence;
static uint32_t artiq_pmu_last_generation;
static inline void artiq_pmu_order(void) {
#ifdef __MICROBLAZE__
 __asm__ volatile("mbar 1" ::: "memory");
#else
 __asm__ volatile("" ::: "memory");
#endif
}
static inline void artiq_pmu_poll_request(void) {
 uint32_t gen=artiq_pmu_request.generation;
 if (!gen || (gen&1) || gen==artiq_pmu_last_generation) return;
 artiq_pmu_order();
 uint32_t nlo=artiq_pmu_request.nonce_lo, nhi=artiq_pmu_request.nonce_hi;
 uint32_t slo=artiq_pmu_request.sequence_lo, shi=artiq_pmu_request.sequence_hi;
 uint32_t kind=artiq_pmu_request.kind, sum=artiq_pmu_request.checksum;
 uint32_t reserved=artiq_pmu_request.reserved;
 artiq_pmu_order();
 if (gen!=artiq_pmu_request.generation || reserved || kind!=1 || !(nlo|nhi)) return;
 if (sum!=(UINT32_C(0x504d5551)^gen^nlo^nhi^slo^shi^kind)) return;
 uint64_t seq=((uint64_t)shi<<32)|slo;
 if (!seq || seq<=artiq_pmu_last_sequence) return;
 artiq_pmu_echo.generation=0;
 artiq_pmu_order();
 artiq_pmu_echo.nonce_lo=nlo;artiq_pmu_echo.nonce_hi=nhi;
 artiq_pmu_echo.sequence_lo=slo;artiq_pmu_echo.sequence_hi=shi;
 artiq_pmu_echo.status=1; /* OBSERVED ONLY: never PARKED/QUIESCENT. */
 artiq_pmu_echo.ack=0;artiq_pmu_echo.reserved=0;
 artiq_pmu_last_sequence=seq;artiq_pmu_last_generation=gen;
 artiq_pmu_order();artiq_pmu_echo.generation=gen;
}
#endif
