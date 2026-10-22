"""Actual transport callbacks with explicit host-only platform stubs; LGPL-3.0-or-later."""
import re,subprocess,tempfile,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]


class Disconnect(unittest.TestCase):
    def test_partial_eof_error_bad_reply_and_complete_reply(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'lwip').mkdir()
            for name in ('lwip/tcp.h','xil_cache.h','xil_printf.h'):(root/name).write_text('')
            source=(REPO/'boards/genesys_zu-5ev/2_firmware_a53/c/kernel_lwip.c').read_text()
            # Only architecture primitives replaced; byte/receive/failed/command/flush remain original.
            source=source.replace('asm volatile("mrs %0,cntpct_el0":"=r"(v))','v=1').replace('asm volatile("mrs %0,cntfrq_el0":"=r"(v))','v=1')
            source=re.sub(r'asm volatile\([^;]+;', '(void)0;',source)
            pre=r'''
#define _GNU_SOURCE
#include <sys/mman.h>
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
typedef int err_t;typedef unsigned short u16_t;
struct tcp_pcb {int fixture;};
struct pbuf {struct pbuf *next;void *payload;u16_t len,tot_len;};
#define ERR_OK 0
#define ERR_ABRT -1
#define ERR_MEM -2
#define TCP_WRITE_FLAG_COPY 1
#define IPADDR_TYPE_V4 0
#define IP_ANY_TYPE 0
static int aborts,closes,frees;
#define tcp_arg(...) ((void)0)
#define tcp_recv(...) ((void)0)
#define tcp_sent(...) ((void)0)
#define tcp_poll(...) ((void)0)
#define tcp_err(...) ((void)0)
#define tcp_accept(...) ((void)0)
#define tcp_recved(...) ((void)0)
#define tcp_sndbuf(...) 8192
#define tcp_write(...) ERR_OK
#define tcp_output(...) ERR_OK
#define tcp_close(...) (++closes,ERR_OK)
#define tcp_abort(...) (++aborts)
#define tcp_new_ip_type(...) ((struct tcp_pcb *)0)
#define tcp_bind(...) ERR_OK
#define tcp_listen(p) (p)
#define pbuf_free(...) (++frees)
#define Xil_DCacheFlushRange(...) ((void)0)
#define Xil_DCacheInvalidateRange(...) ((void)0)
#define xil_printf(...) ((void)0)
void artiq_runtime_kernel_ready(void) {}
void artiq_runtime_kernel_event(const uint8_t *p,size_t n) {(void)p;(void)n;}
'''
            post=r'''
static struct tcp_pcb fixture;
static void setup(void) {
 owner=&fixture;pending=0;busy=3;dead=recovering=closing=0;mode=6;
 cmd_seq=0;aborts=closes=frees=0;write_mb(4,0);genesys_rpc_reply_init(&rpc_reply);
}
static err_t input(uint8_t *p,size_t n,err_t e) {
 struct pbuf b={NULL,p,n,n};return receive(NULL,&fixture,&b,e);
}
int main(void) {
 void *m=mmap((void *)0x200ff000,0x1000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
 assert(m==(void *)0x200ff000);
 m=mmap((void *)0x21000000,0x1000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
 assert(m==(void *)0x21000000);
 uint8_t reply[]={1,0,0,0,'i',42,0,0,0};
 setup();assert(input(reply,6,ERR_OK)==ERR_OK);assert(cmd_seq==0&&busy==3);
 assert(receive(NULL,&fixture,NULL,ERR_OK)==ERR_OK);
 assert(read_mb(4)==5&&dead&&busy==0&&owner==NULL&&closes==1);
 setup();assert(input(reply,6,ERR_MEM)==ERR_ABRT);
 assert(read_mb(4)==5&&dead&&busy==0&&owner==NULL&&aborts==1&&frees==1);
 setup();uint8_t bad[]={0,0,0,0};assert(input(bad,4,ERR_OK)==ERR_ABRT);
 assert(read_mb(4)==5&&dead&&aborts==1&&frees==1);
 setup();assert(input(reply,6,ERR_OK)==ERR_OK);assert(input(reply+6,3,ERR_OK)==ERR_OK);
 assert(read_mb(4)==4&&read_mb(8)==4&&busy==2&&!dead&&cmd_seq==1&&*(uint32_t *)INPUT==42);
 return 0;
}
'''
            p=root/'probe.c';p.write_text(pre+source+post);exe=root/'probe'
            subprocess.run(['cc','-std=c11','-I',str(root),'-I',str(REPO/'boards/genesys_zu-5ev/2_firmware_a53/c'),str(p),'-o',str(exe)],capture_output=True,check=True)
            subprocess.run([str(exe)],capture_output=True,check=True)

if __name__=='__main__':unittest.main()
