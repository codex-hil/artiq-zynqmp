/* Bounded scalar RPC reply-body parser; LGPL-3.0-or-later.
 * Input starts after Request.RPCReply; no allocation, mailbox or network access. */
#ifndef GENESYS_RPC_REPLY_H
#define GENESYS_RPC_REPLY_H
#include <stdint.h>
#include <stddef.h>
struct genesys_rpc_reply {
 uint32_t length;
 size_t offset, expected;
 uint8_t payload[8];
 int state;
};
static inline void genesys_rpc_reply_init(struct genesys_rpc_reply *p) {
 *p=(struct genesys_rpc_reply){0};
}
/* -1 invalid (sticky), 0 incomplete, 1 complete. Call init before reuse. */
static inline int genesys_rpc_reply_byte(struct genesys_rpc_reply *p,uint8_t b) {
 if(p->state==0) {
  p->length|=(uint32_t)b<<(8*p->offset++);
  if(p->offset==4) {
   p->offset=0;
   if(p->length!=1){p->state=-1;return -1;}
   p->state=1;
  }
  return 0;
 }
 if(p->state==1) {
  if(b=='n')p->expected=0;
  else if(b=='b')p->expected=1;
  else if(b=='i'||b=='u')p->expected=4;
  else if(b=='I'||b=='U'||b=='f')p->expected=8;
  else {p->state=-1;return -1;}
  p->state=p->expected?2:3;
  return p->expected?0:1;
 }
 if(p->state==2) {
  p->payload[p->offset++]=b;
  if(p->offset==p->expected){p->state=3;return 1;}
  return 0;
 }
 p->state=-1;return -1;
}
#endif
