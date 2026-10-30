/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_mmio_read.h"
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_MMIO_AUDIT_ONLY)
#error "PIT MMIO requires explicit MicroBlaze audit-only opt-in; not deployable"
#endif
int pit_mmio_read(void *context, uint32_t address, uint32_t *out)
{
    uint32_t value;
    if(context || !out) return -1;
    switch(address) {
    case UINT32_C(0xffd40044):
    case UINT32_C(0xffd40054):
    case UINT32_C(0xffd40064):
    case UINT32_C(0xffd40074): break;
    default: return -1;
    }
    value=*(volatile const uint32_t *)(uintptr_t)address;
    *out=value;
    return 0;
}
