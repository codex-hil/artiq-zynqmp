/* Thin ARTIQ TCP framing and cache-aware bridge to the Rust CPU1 worker.
 * Foreground lwIP RAW callbacks only. One kernel owner, independent management. */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "lwip/tcp.h"
#include "xil_cache.h"
#include "xil_printf.h"
#define MAILBOX 0x200ff000UL
#define INPUT 0x21000000UL
#define KERNEL_MAX_INPUT (1024u*1024u)
#define BODY (MAILBOX+256)
#define BODY_MAX 4096u
static struct tcp_pcb *owner;
static uint8_t output[8192];
static size_t pending;
static uint32_t cmd_seq,seen_event;
static int mode,closing,loaded,busy,dead,recovering;
/* Prevent CPU0 diagnostic access to the shared RTIO counter latch while CPU1 runs. */
int genesys_kernel_running(void) { return busy != 0 || dead || recovering; }
static size_t count,total;
static uint32_t length;
static uint8_t operation,return_tag;
static uint64_t started;
static const char magic[]="ARTIQ coredev\n";
extern void artiq_runtime_kernel_ready(void);
extern void artiq_runtime_kernel_event(const uint8_t *,size_t);
static void log_event(const char *s) {artiq_runtime_kernel_event((const uint8_t *)s,strlen(s));}
static uint64_t ticks(void) {uint64_t v;asm volatile("mrs %0,cntpct_el0":"=r"(v));return v;}
static uint64_t frequency(void) {uint64_t v;asm volatile("mrs %0,cntfrq_el0":"=r"(v));return v;}
static uint32_t read_mb(size_t off) {return *(volatile uint32_t *)(MAILBOX+off);}
static void write_mb(size_t off,uint32_t v) {*(volatile uint32_t *)(MAILBOX+off)=v;}
static void command(uint32_t op,uint32_t n) {
 if(n) Xil_DCacheFlushRange(INPUT,n);
 write_mb(4,op);write_mb(8,n);asm volatile("dsb sy" ::: "memory");
 write_mb(0,++cmd_seq);Xil_DCacheFlushRange(MAILBOX,64);
 asm volatile("dsb sy\nsev" ::: "memory");started=ticks();
}
static err_t receive(void *,struct tcp_pcb *,struct pbuf *,err_t);
static err_t acknowledged(void *,struct tcp_pcb *,u16_t);
static err_t poll(void *,struct tcp_pcb *);
static void failed(void *,err_t);
static void callbacks(void) {tcp_arg(owner,NULL);tcp_recv(owner,receive);tcp_sent(owner,acknowledged);tcp_poll(owner,poll,2);tcp_err(owner,failed);}
static err_t flush(void) {
 if(!owner)return ERR_OK;
 if(pending) {
  size_t n=tcp_sndbuf(owner);if(n>pending)n=pending;
  if(n) {err_t e=tcp_write(owner,output,(u16_t)n,TCP_WRITE_FLAG_COPY);
   if(e==ERR_OK){pending-=n;memmove(output,output+n,pending);tcp_output(owner);}
   else if(e!=ERR_MEM)return e;
  }
 }
 if(closing&&!pending) {
  struct tcp_pcb *p=owner;tcp_arg(p,NULL);tcp_recv(p,NULL);tcp_sent(p,NULL);tcp_poll(p,NULL,0);tcp_err(p,NULL);
  if(tcp_close(p)==ERR_OK)owner=NULL;else callbacks();
 }
 return ERR_OK;
}
static int append(const void *b,size_t n) {if(n>sizeof(output)-pending)return -1;memcpy(output+pending,b,n);pending+=n;return 0;}
static void header(uint8_t type) {const uint8_t h[]={0x5a,0x5a,0x5a,0x5a,type};append(h,sizeof(h));}
static void chunk(const void *b,uint32_t n) {append(&n,4);append(b,n);}
static void error_load(const char *s) {header(6);chunk(s,strlen(s));}
static void failed(void *arg,err_t e) {(void)arg;(void)e;owner=NULL;pending=0;if(busy){command(5,0);dead=1;busy=0;}}
static err_t abort_owner(void) {struct tcp_pcb *p=owner;failed(NULL,ERR_ABRT);tcp_err(p,NULL);tcp_abort(p);return ERR_ABRT;}
static err_t acknowledged(void *arg,struct tcp_pcb *p,u16_t n) {(void)arg;(void)p;(void)n;return flush();}
static err_t poll(void *arg,struct tcp_pcb *p) {(void)arg;(void)p;return flush();}
/* modes: greeting0, sync1, request2, length3, data4, worker-wait5,
 * RPC return length6, RPC return tag7, RPC return value8 */
static int byte(uint8_t b) {
 if(mode==0) {if(b!=(uint8_t)magic[count++])return -1;if(count==sizeof(magic)-1){append("e",1);count=0;mode=1;}return 0;}
 if(mode==1) {count=b==0x5a?count+1:0;if(count==4){mode=2;count=0;}return 0;}
 if(mode==2) {
  operation=b;
  if(b==3) {header(2);append("ARZQ",4);mode=1;}
  else if(b==5) {if(busy)return -1;loaded=0;length=0;count=0;mode=3;}
  else if(b==6) {
   if(!loaded||busy||dead){header(8);closing=1;}else{busy=2;mode=5;command(2,0);}
  } else if(b==8&&busy==3) {total=48;count=0;mode=9;}
  else if(b==7&&busy==3) {length=0;count=0;mode=6;}
  else return -1;
  return 0;
 }
 if(mode==3||mode==6) {
  length|=(uint32_t)b<<(count++*8);
  if(count==4) {
   count=0;
   if(mode==3) {if(length==0||length>KERNEL_MAX_INPUT){error_load("kernel upload exceeds 1 MiB or is empty");closing=1;return 0;}mode=4;}
   else {if(length!=1)return -1;mode=7;}
  }return 0;
 }
 if(mode==4) {
  ((uint8_t *)INPUT)[count++]=b;
  if(count==length){count=0;mode=5;if(dead||recovering){error_load("CPU1 unavailable; restart worker");mode=1;}else{busy=1;command(1,length);}}
  return 0;
 }
 if(mode==7) {
  return_tag=b;
  if(b=='n')total=0;else if(b=='b')total=1;else if(b=='i'||b=='u')total=4;else if(b=='I'||b=='U'||b=='f')total=8;else return -1;
  mode=8;count=0;
  if(!total){command(4,0);busy=2;mode=5;}
  return 0;
 }
 if(mode==9) {
  ((uint8_t *)INPUT)[count++]=b;
  if(count==total){command(7,total);busy=2;mode=5;count=0;}
  return 0;
 }
 if(mode==8) {
  ((uint8_t *)INPUT)[count++]=b;
  if(count==total){command(4,total);busy=2;mode=5;count=0;}
  return 0;
 }
 return -1;
}
static err_t receive(void *arg,struct tcp_pcb *p,struct pbuf *data,err_t error) {
 (void)arg;(void)p;
 if(!data){if(busy){command(5,0);dead=1;busy=0;}closing=1;return flush();}
 if(error!=ERR_OK){pbuf_free(data);return abort_owner();}
 for(struct pbuf *q=data;q&&!closing;q=q->next){const uint8_t *b=q->payload;
  for(size_t i=0;i<q->len&&!closing;i++)if(byte(b[i])){pbuf_free(data);return abort_owner();}
 }
 tcp_recved(owner,data->tot_len);pbuf_free(data);return flush();
}
void genesys_kernel_poll(void) {
 Xil_DCacheInvalidateRange(MAILBOX+64,64);
 uint32_t event=read_mb(64);
 if(event!=seen_event) {
  asm volatile("dsb sy" ::: "memory");seen_event=event;
  uint32_t status=read_mb(68),n=read_mb(72);
  if(n>BODY_MAX){dead=1;if(owner)abort_owner();return;}
  Xil_DCacheInvalidateRange(BODY,BODY_MAX);
  if(status==1&&recovering) {recovering=0;log_event("CPU1 worker recovered after kernel exception.\n");}
  if(owner&&busy) {
   if(status==2&&busy==1){log_event("CPU1 kernel ELF relocated and loaded.\n");header(5);loaded=1;busy=0;mode=1;}
   else if(status==3&&busy==1){log_event("CPU1 kernel load rejected.\n");header(6);chunk((void *)BODY,n);busy=0;mode=1;}
   else if(status==4&&busy==2){log_event("CPU1 kernel finished.\n");header(7);append((void *)BODY,n);busy=0;mode=1;}
   else if(status==8&&busy==2){log_event("CPU1 uncaught kernel exception.\n");header(9);append((void *)BODY,n);loaded=0;busy=0;mode=1;recovering=1;command(6,0);}
   else if((status==5||status==6)&&busy==2){
    log_event("CPU1 kernel RPC request.\n");header(10);if(append((void *)BODY,n)){abort_owner();return;}
    if(status==5){command(3,0);}else{busy=3;mode=1;count=0;}
   } else {header(8);closing=1;busy=0;dead=1;}
   if(flush()!=ERR_OK)abort_owner();
  }
 }
 if(busy&&ticks()-started>frequency()*30){dead=1;busy=0;if(owner){header(8);closing=1;flush();}}
}
static err_t accepted(void *arg,struct tcp_pcb *p,err_t error) {
 (void)arg;if(error!=ERR_OK)return error;
 if(owner){tcp_abort(p);return ERR_ABRT;}
 owner=p;pending=0;mode=0;closing=loaded=0;count=0;callbacks();return ERR_OK;
}
int genesys_kernel_start(void) {
 Xil_DCacheInvalidateRange(MAILBOX+64,64);
 if(read_mb(68)!=1||!frequency())return -1;
 seen_event=read_mb(64);cmd_seq=read_mb(0);
 struct tcp_pcb *p=tcp_new_ip_type(IPADDR_TYPE_V4);if(!p)return -1;
 if(tcp_bind(p,IP_ANY_TYPE,1381)!=ERR_OK){tcp_close(p);return -1;}
 p=tcp_listen(p);if(!p)return -1;tcp_accept(p,accepted);
 artiq_runtime_kernel_ready();
 xil_printf("GENESYS kernel transport @ port 1381; CPU1 loader/RPC; RTIO capabilities depend on worker\r\n");return 0;
}
