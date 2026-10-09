/* ARTIQ analyzer/moninj transport over the maintained foreground AMD/lwIP loop.
 * LGPL-3.0-or-later. Analyzer storage is the finite bring-up BRAM ring. */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "lwip/tcp.h"
#include "xil_printf.h"
#include "sleep.h"
#include "debug_csr.h"

static void wr(uintptr_t a,uint32_t v){*(volatile uint32_t *)a=v;__asm__ volatile("dsb sy" ::: "memory");}
static uint32_t rd(uintptr_t a){__asm__ volatile("dsb sy" ::: "memory");return *(volatile uint32_t *)a;}
static void be32(uint8_t *p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(24-8*i));}
static void be64(uint8_t *p,uint64_t v){for(unsigned i=0;i<8;i++)p[i]=(uint8_t)(v>>(56-8*i));}
static void le32(uint8_t *p,uint32_t v){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i));}
static void le64(uint8_t *p,uint64_t v){for(unsigned i=0;i<8;i++)p[i]=(uint8_t)(v>>(8*i));}
static uint32_t fromle(const uint8_t *p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
struct debug_connection {
 struct tcp_pcb *pcb;
 uint8_t out[9000],packet[7],probe[2],injection[2];
 uint8_t last_probe[2],last_injection[2];
 size_t pending,header,used,need;
 int close,analyzer;
};
static struct debug_connection clients[2];
static err_t recv_cb(void *,struct tcp_pcb *,struct pbuf *,err_t);
static err_t sent_cb(void *,struct tcp_pcb *,u16_t);
static err_t poll_cb(void *,struct tcp_pcb *);
static void error_cb(void *,err_t);
static void release_override(void){wr(MON_INJ_CHAN,0);wr(MON_INJ_SEL,0);wr(MON_INJ_VALUE,0);}
static void callbacks(struct debug_connection *c){tcp_arg(c->pcb,c);tcp_recv(c->pcb,recv_cb);tcp_sent(c->pcb,sent_cb);tcp_poll(c->pcb,poll_cb,1);tcp_err(c->pcb,error_cb);}
static err_t flush(struct debug_connection *c){
 if(c->pending){
  size_t n=tcp_sndbuf(c->pcb);if(n>c->pending)n=c->pending;
  if(n){err_t r=tcp_write(c->pcb,c->out,(u16_t)n,TCP_WRITE_FLAG_COPY);
   if(r!=ERR_OK)return r==ERR_MEM?ERR_OK:r;
   c->pending-=n;memmove(c->out,c->out+n,c->pending);tcp_output(c->pcb);
  }
 }
 if(c->close&&!c->pending){
  struct tcp_pcb *p=c->pcb;tcp_arg(p,NULL);tcp_recv(p,NULL);tcp_sent(p,NULL);tcp_poll(p,NULL,0);tcp_err(p,NULL);
  if(tcp_close(p)==ERR_OK){if(!c->analyzer)release_override();c->pcb=NULL;}else callbacks(c);
 }
 return ERR_OK;
}
static err_t abort_client(struct debug_connection *c){struct tcp_pcb *p=c->pcb;if(!c->analyzer)release_override();tcp_arg(p,NULL);tcp_err(p,NULL);c->pcb=NULL;tcp_abort(p);return ERR_ABRT;}
static void error_cb(void *arg,err_t e){(void)e;struct debug_connection *c=arg;if(c){if(!c->analyzer)release_override();c->pcb=NULL;}}
static err_t sent_cb(void *arg,struct tcp_pcb *p,u16_t n){(void)p;(void)n;return flush(arg);}
static int queue(struct debug_connection *c,const uint8_t *p,size_t n){if(n>sizeof(c->out)-c->pending)return -1;memcpy(c->out+c->pending,p,n);c->pending+=n;return 0;}
static uint8_t probe(unsigned ch){wr(MON_CHAN,ch);wr(MON_SEL,0);wr(MON_UPDATE,1);usleep(10);return rd(MON_VALUE)&1;}
static uint8_t injection(unsigned ov){wr(MON_INJ_CHAN,0);wr(MON_INJ_SEL,ov);return rd(MON_INJ_VALUE)&1;}
static int report_probe(struct debug_connection *c,unsigned ch){uint8_t p[14]={0};le32(p+1,ch);p[5]=0;uint8_t v=probe(ch);le64(p+6,v);c->last_probe[ch]=v;return queue(c,p,sizeof(p));}
static int report_injection(struct debug_connection *c,unsigned ov){uint8_t p[7]={1};le32(p+1,0);p[5]=ov;uint8_t v=injection(ov);p[6]=v;c->last_injection[ov]=v;return queue(c,p,sizeof(p));}
static int command(struct debug_connection *c){
 uint8_t *p=c->packet;unsigned type=p[0];
 unsigned ch=fromle(p+(type==0||type==3?2:1));unsigned sel=p[type==0||type==3?6:5];
 if(type==0){if(ch>1||sel!=0||p[1]>1)return -1;c->probe[ch]=p[1];if(p[1])return report_probe(c,ch);}
 else if(type==3){if(ch!=0||sel>1||p[1]>1)return -1;c->injection[sel]=p[1];if(p[1])return report_injection(c,sel);}
 else if(type==1){if(ch!=0||sel>1||p[6]>1)return -1;wr(MON_INJ_CHAN,0);wr(MON_INJ_SEL,sel);wr(MON_INJ_VALUE,p[6]);}
 else if(type==2){if(ch!=0||sel>1)return -1;return report_injection(c,sel);}
 else return -1;
 return 0;
}
static err_t poll_cb(void *arg,struct tcp_pcb *p){
 (void)p;struct debug_connection *c=arg;
 if(!c->analyzer&&c->header==sizeof("ARTIQ moninj\n")-1&&!c->close){
  for(unsigned i=0;i<2;i++){
   if(c->probe[i]&&probe(i)!=c->last_probe[i]&&report_probe(c,i))return abort_client(c);
   if(c->injection[i]&&injection(i)!=c->last_injection[i]&&report_injection(c,i))return abort_client(c);
  }
 }
 return flush(c);
}
static err_t recv_cb(void *arg,struct tcp_pcb *pcb,struct pbuf *p,err_t e){
 (void)pcb;struct debug_connection *c=arg;
 if(!p){c->close=1;return flush(c);}if(e!=ERR_OK){pbuf_free(p);return abort_client(c);}
 const char magic[]="ARTIQ moninj\n";
 for(struct pbuf *q=p;q;q=q->next){const uint8_t *data=q->payload;
  for(size_t i=0;i<q->len;i++){
   uint8_t b=data[i];
   if(c->analyzer){pbuf_free(p);return abort_client(c);}
   if(c->header<sizeof(magic)-1){if(b!=(uint8_t)magic[c->header++]){pbuf_free(p);return abort_client(c);}continue;}
   if(!c->used){if(b>3){pbuf_free(p);return abort_client(c);}c->need=b==2?6:7;}
   c->packet[c->used++]=b;
   if(c->used==c->need){if(command(c)){pbuf_free(p);return abort_client(c);}c->used=0;}
  }
 }
 tcp_recved(c->pcb,p->tot_len);pbuf_free(p);return flush(c);
}
static int analyzer_dump(struct debug_connection *c){
 wr(AN_ENABLE,0);usleep(10);
 uint64_t count=((uint64_t)rd(AN_COUNT)<<32)|rd(AN_COUNT+4);
 uint32_t depth=rd(AN_DEPTH);if(depth!=256)return -1;
 uint32_t n=count>depth?depth:(uint32_t)count;
 uint32_t first=count>depth?(uint32_t)(count%depth):0;
 c->out[0]='E';be32(c->out+1,n*32);be64(c->out+5,count*32);
 c->out[13]=(uint8_t)rd(AN_OVERFLOW);c->out[14]=255;c->out[15]=0;
 for(unsigned i=0;i<n;i++){
  wr(AN_INDEX,(first+i)%depth);usleep(1);wr(AN_UPDATE,1);
  for(unsigned j=0;j<8;j++)be32(c->out+16+32*i+4*j,rd(AN_DATA+4*j));
 }
 c->pending=16+n*32;c->close=1;
 wr(AN_CLEAR,1);wr(AN_OVERFLOW_RESET,1);wr(AN_ENABLE,1);
 return 0;
}
static err_t accept_cb(void *arg,struct tcp_pcb *pcb,err_t e){
 if(e!=ERR_OK)return e;
 int analyzer=(int)(uintptr_t)arg;
 struct debug_connection *c=&clients[analyzer?1:0];
 if(c->pcb){tcp_abort(pcb);return ERR_ABRT;}
 memset(c,0,sizeof(*c));c->pcb=pcb;c->analyzer=analyzer;callbacks(c);
 if(analyzer&&analyzer_dump(c))return abort_client(c);
 return flush(c);
}
int genesys_debug_start(void){
 for(unsigned i=0;i<2;i++){
  struct tcp_pcb *p=tcp_new_ip_type(IPADDR_TYPE_V4);if(!p)return -1;
  if(tcp_bind(p,IP_ANY_TYPE,i?1382:1383)!=ERR_OK){tcp_close(p);return -1;}
  p=tcp_listen(p);if(!p)return -1;tcp_arg(p,(void *)(uintptr_t)i);tcp_accept(p,accept_cb);
 }
 xil_printf("GENESYS ARTIQ analyzer1382 moninj1383 ready, BRAM256\r\n");return 0;
}
