/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef PIT_TERMINAL_BUILD_H
#define PIT_TERMINAL_BUILD_H
#include "pit_terminal_record.h"
struct pit_terminal_observations {
    uint32_t called_mask; /* bit0 before, bit1 checked, bit2 final */
    int32_t returns[3]; /* zero success; failed callback output is ignored */
    uint32_t msr[3];
    uint32_t sample_outcome; /* 1 IRQ unproven, 2 read failure, 3 publication unknown, 4 complete */
};
/* Caller owns distinct aligned inputs/output. Hashes are EXTERNAL, not computed
 * or authenticated here. Pure offline metadata builder, no publication/HW.
 * Returns 0 on success, -1 without output writes on invalid input.
 */
int pit_terminal_build(struct pit_terminal_record *, const struct pit_terminal_observations *,
                       uint64_t, const uint32_t image_sha256_le[8], const uint32_t *sample_sha256_le);
#endif
