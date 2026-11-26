/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include "master_network_fault_latch.h"
/* COPY-ONLY experiment. Definition/lifetime/coherent-memory qualification must
 * be provided independently. No definition or production ISR hook is installed.
 * Only publication: no owner policy, IRQ mask/reset or recovery control here.
 */
extern struct mnf_latch mnf_copy_only_gem_fault;
static inline void mnf_copy_gem_fault_publish(unsigned error_word){
 if(error_word)mnf_publish(&mnf_copy_only_gem_fault);
}
