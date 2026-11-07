/* SPDX-License-Identifier: LGPL-3.0-or-later
 * Compile-only callback API wrappers. No entry, direct MMIO or core assignment.
 */
#include "reset_driver.h"
struct gr_result gr_compile_assert(const struct gm_bus *bus,uint32_t limit) {
 return gr_assert_reset(bus,limit);
}
struct gr_result gr_compile_release(const struct gm_bus *bus,uint32_t limit,uint32_t abandoned) {
 return gr_release_reset(bus,limit,abandoned);
}
