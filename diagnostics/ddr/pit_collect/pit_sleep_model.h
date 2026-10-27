/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_SLEEP_MODEL_H
#define PIT_SLEEP_MODEL_H
#include "pit_capture.h"
/* OFFLINE lifecycle model only: returning terminal callback is NOT PMU sleep.
 * No MicroBlaze intrinsics, MMIO adapter, runtime hook or physical entry point.
 * Each callback must return; hung instruction handling remains outside model.
 */
typedef int (*pit_msr_fn)(void *, uint32_t *);
typedef int (*pit_disable_fn)(void *);
typedef void (*pit_terminal_model_fn)(void *, int);
enum pit_sleep_status { PIT_SLEEP_REJECTED, PIT_SLEEP_IRQ_UNPROVEN,
                        PIT_SLEEP_READ_FAILED, PIT_SLEEP_PUBLICATION_UNKNOWN,
                        PIT_SLEEP_CAPTURE_COMPLETE };
struct pit_sleep_ops {
    pit_msr_fn msr;
    pit_disable_fn disable;
    pit_read_fn read;
    pit_write_fn write;
    pit_barrier_fn barrier;
    pit_terminal_model_fn terminal;
};
enum pit_sleep_status pit_sleep_model(struct pit_capture_attempt *, uint64_t,
                                     const struct pit_sleep_ops *, void *);
#endif
