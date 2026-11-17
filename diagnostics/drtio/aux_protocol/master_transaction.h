/* SPDX-License-Identifier: LGPL-3.0-or-later */
#pragma once
#include <stdint.h>
/* Host-only policy candidate. Caller exclusively owns one link and provides
 * decoded CRC-checked packets. RoutingAck has no transaction ID: matching kind
 * alone cannot reject stale ACKs. Init requires a NEW externally qualified
 * reset/drained link epoch, never a timeout retry. No MMIO or transport here.
 */
enum mt_state {MT_IDLE,MT_TX,MT_WAIT,MT_DONE,MT_FAILED};
enum mt_result {MT_OK=0,MT_INVALID=-1,MT_BUSY=-2,MT_IO=-3,
 MT_UNEXPECTED=-4,MT_TIMEOUT=-5,MT_PACKET=-6};
struct mt_transaction {enum mt_state state;int result;uint32_t left,expected,commit_attempted;};
static inline void mt_init_new_epoch(struct mt_transaction *t) {
 if(t)*t=(struct mt_transaction){MT_IDLE,MT_OK,0,0,0};
}
static inline int mt_begin(struct mt_transaction *t,uint32_t request,uint32_t budget) {
 if(!t||!budget||budget>4096||(request!=0x30&&request!=0x31))return MT_INVALID;
 if(t->state!=MT_IDLE)return MT_BUSY;
 /* Mark possible commit BEFORE caller invokes transport. Never resend here. */
 t->state=MT_TX;t->left=budget;t->expected=0x32;t->commit_attempted=1;return MT_OK;
}
static inline int mt_tx_complete(struct mt_transaction *t,int transport_ok) {
 if(!t||t->state!=MT_TX)return MT_INVALID;
 if(!transport_ok){t->state=MT_FAILED;t->result=MT_IO;return MT_IO;}
 t->state=MT_WAIT;return MT_OK;
}
/* packet=0: no packet; packet=1: valid decoded kind; other: malformed/CRC error.
 * One call consumes one budget unit. A valid ACK on the last unit succeeds.
 * Budget units are caller polling steps, NOT milliseconds or hardware bound.
 */
static inline int mt_poll(struct mt_transaction *t,int packet,uint32_t kind) {
 if(!t||t->state!=MT_WAIT)return MT_INVALID;
 int error=MT_OK;
 if(packet!=0&&packet!=1)error=MT_PACKET;
 else if(packet==1){
  if(kind==t->expected){t->state=MT_DONE;return MT_OK;}
  error=MT_UNEXPECTED;
 } else if(--t->left==0)error=MT_TIMEOUT;
 if(error){t->state=MT_FAILED;t->result=error;}
 return error;
}
