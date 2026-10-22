/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef TEST_XIICPS_H
#define TEST_XIICPS_H
#include <stdint.h>
typedef uint32_t u32;typedef int32_t s32;typedef uint16_t u16;typedef uint8_t u8;
#define XIL_COMPONENT_IS_READY 0x11111111U
#define XIICPS_EVENT_COMPLETE_SEND 1U
#define XIICPS_EVENT_COMPLETE_RECV 2U
#define XIICPS_EVENT_NACK 32U
#define XIICPS_EVENT_ERROR 8U
typedef struct {
 struct {uintptr_t BaseAddress;} Config;
 u32 IsReady;int IsRepeatedStart,Is10BitAddr; s32 RecvByteCount,SendByteCount;
 void (*handler)(void *,u32);void *ref;
} XIicPs;
int XIicPs_BusIsBusy(XIicPs *);
void XIicPs_SetStatusHandler(XIicPs *,void *,void (*)(void *,u32));
void XIicPs_MasterRecv(XIicPs *,u8 *,s32,u16);
void XIicPs_MasterSend(XIicPs *,u8 *,s32,u16);
void XIicPs_MasterInterruptHandler(XIicPs *);
void XIicPs_DisableAllInterrupts(uintptr_t);
#endif
