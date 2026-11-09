/* SPDX-License-Identifier: LGPL-3.0-or-later
 * Compile-only callback API wrappers. No entry, direct MMIO or core assignment.
 */
#include "shape_recovery.h"
struct gr_result gr_compile_assert(const struct gm_bus *bus,uint32_t limit) {
 return gr_assert_reset(bus,limit);
}
struct gr_result gr_compile_release(const struct gm_bus *bus,uint32_t limit,uint32_t abandoned) {
 return gr_release_reset(bus,limit,abandoned);
}
int gr_compile_shape_status(const struct gm_bus *bus,uint32_t capability,uint32_t *fault) {
 return gr_shape_status(bus,capability,fault);
}
struct gsr_result gr_compile_shape_recover(const struct gm_bus *bus,uint32_t limit,
 uint32_t capability,uint32_t abandoned,uint32_t withdrawn) {
 return gsr_recover(bus,limit,capability,abandoned,withdrawn);
}
