/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "xil_io.h"
__attribute__((noinline)) u32 bsp_read(UINTPTR address) { return Xil_In32(address); }
__attribute__((noinline)) void bsp_write(UINTPTR address, u32 value) { Xil_Out32(address, value); }
__attribute__((noinline)) void bsp_barrier(void) { DATA_SYNC; }
__attribute__((noinline)) void explicit_barrier(void) { __asm__ __volatile__("mbar 1" ::: "memory"); }
u32 bsp_load_pair(u32 *p) { u32 a = *p; DATA_SYNC; return a + *p; }
u32 explicit_load_pair(u32 *p) { u32 a = *p; __asm__ __volatile__("mbar 1" ::: "memory"); return a + *p; }
