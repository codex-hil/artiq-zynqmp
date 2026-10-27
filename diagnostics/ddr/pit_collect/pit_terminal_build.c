/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_terminal_build.h"
int pit_terminal_build(struct pit_terminal_record *out, const struct pit_terminal_observations *obs,
                       uint64_t nonce, const uint32_t image[8], const uint32_t *sample)
{
    uint32_t valid = 0, image_nonzero = 0, sample_nonzero = 0, status;
    unsigned i;
    int initial_ok;
    if (!out || !obs || !nonce || !image || (obs->called_mask != 0 && obs->called_mask != 1 && obs->called_mask != 3 && obs->called_mask != 7) ||
        obs->sample_outcome < 1 || obs->sample_outcome > 4) return -1;
    for (i = 0; i < 3; ++i)
        if ((obs->called_mask & (1u << i)) && !obs->returns[i]) valid |= 1u << i;
    initial_ok = (valid & 3) == 3 && obs->msr[1] == (obs->msr[0] & ~UINT32_C(2));
    if (!initial_ok && (obs->sample_outcome != 1 || sample)) return -1;
    if ((obs->sample_outcome == 1 || obs->sample_outcome == 2) && sample) return -1;
    if (obs->sample_outcome == 4 && !sample) return -1;
    for (i = 0; i < 8; ++i) {
        image_nonzero |= image[i];
        if (sample) sample_nonzero |= sample[i];
    }
    if (!image_nonzero || (sample && !sample_nonzero)) return -1;
    status = obs->sample_outcome;
    if (!initial_ok || !(valid & 4) || obs->msr[2] != obs->msr[1]) status = 1;
    out->commit = 1; out->magic = PIT_TERMINAL_MAGIC; out->version = 1;
    out->status = status; out->nonce = nonce;
    out->checked_msr = valid & 2 ? obs->msr[1] : 0;
    out->final_msr = valid & 4 ? obs->msr[2] : 0;
    for (i = 0; i < 8; ++i) {
        ((volatile uint32_t *)out->image_sha256_le)[i] = image[i];
        ((volatile uint32_t *)out->sample_sha256_le)[i] = sample ? sample[i] : 0;
    }
    return 0;
}
