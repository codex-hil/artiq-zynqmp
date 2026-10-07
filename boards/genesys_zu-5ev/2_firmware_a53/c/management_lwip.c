/* Network ownership stays in maintained AMD/lwIP; protocol logic is Rust.
 * Call Rust exclusively from the single-core foreground lwIP callback loop. */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "lwip/tcp.h"
#include "xil_printf.h"
#include "rtio_csr.h"

extern size_t artiq_session_size(void);
extern size_t artiq_session_align(void);
extern void artiq_session_init(void *);
extern int32_t artiq_session_byte(void *, uint8_t, uint8_t *, size_t);
extern int32_t artiq_session_closing(const void *);
extern void artiq_runtime_ready(const uint8_t *, size_t);

uint64_t genesys_rtio_counter(void) {
    *(volatile uint32_t *)(uintptr_t)RTIO_COUNTER_UPDATE = 1;
    __asm__ volatile("dsb sy" ::: "memory");
    uint32_t high = *(volatile uint32_t *)(uintptr_t)RTIO_COUNTER;
    uint32_t low = *(volatile uint32_t *)(uintptr_t)(RTIO_COUNTER + 4);
    return ((uint64_t)high << 32) | low;
}

struct connection {
    struct tcp_pcb *pcb;
    _Alignas(16) uint8_t state[256];
    uint8_t output[8192];
    size_t pending;
    int closing;
};
static struct connection connections[4];
static err_t received(void *, struct tcp_pcb *, struct pbuf *, err_t);
static err_t sent(void *, struct tcp_pcb *, u16_t);
static err_t polled(void *, struct tcp_pcb *);
static void failed(void *, err_t);

static void callbacks(struct connection *c) {
    tcp_arg(c->pcb, c);
    tcp_recv(c->pcb, received);
    tcp_sent(c->pcb, sent);
    tcp_poll(c->pcb, polled, 2);
    tcp_err(c->pcb, failed);
}
static err_t flush(struct connection *c) {
    if (c->pending) {
        size_t n = tcp_sndbuf(c->pcb);
        if (n > c->pending) n = c->pending;
        if (n) {
            err_t status = tcp_write(c->pcb, c->output, (u16_t)n, TCP_WRITE_FLAG_COPY);
            if (status == ERR_OK) {
                c->pending -= n;
                memmove(c->output, c->output + n, c->pending);
                tcp_output(c->pcb);
            } else if (status != ERR_MEM) return status;
        }
    }
    if (c->closing && !c->pending) {
        struct tcp_pcb *pcb = c->pcb;
        tcp_arg(pcb, NULL);
        tcp_recv(pcb, NULL);
        tcp_sent(pcb, NULL);
        tcp_poll(pcb, NULL, 0);
        tcp_err(pcb, NULL);
        if (tcp_close(pcb) == ERR_OK) c->pcb = NULL;
        else callbacks(c); /* Retry FIN allocation on ACK/poll. */
    }
    return ERR_OK;
}
static void failed(void *arg, err_t error) {
    (void)error;
    struct connection *c = arg;
    if (c) { c->pcb = NULL; c->pending = 0; }
}
static err_t abort_connection(struct connection *c) {
    struct tcp_pcb *pcb = c->pcb;
    tcp_arg(pcb, NULL);
    tcp_err(pcb, NULL);
    c->pcb = NULL;
    c->pending = 0;
    tcp_abort(pcb);
    return ERR_ABRT;
}
static err_t sent(void *arg, struct tcp_pcb *pcb, u16_t count) {
    (void)pcb; (void)count;
    struct connection *c = arg;
    return flush(c);
}
static err_t polled(void *arg, struct tcp_pcb *pcb) {
    (void)pcb;
    return flush(arg);
}
static err_t received(void *arg, struct tcp_pcb *pcb, struct pbuf *p, err_t error) {
    struct connection *c = arg;
    (void)pcb;
    if (!p) { c->closing = 1; return flush(c); }
    if (error != ERR_OK) { pbuf_free(p); return abort_connection(c); }
    uint8_t reply[2048];
    for (struct pbuf *q = p; q && !c->closing; q = q->next) {
        const uint8_t *data = q->payload;
        for (size_t i = 0; i < q->len && !c->closing; i++) {
            int32_t n = artiq_session_byte(c->state, data[i], reply, sizeof(reply));
            if (n < 0 || (size_t)n > sizeof(reply) || (size_t)n > sizeof(c->output) - c->pending) {
                pbuf_free(p);
                return abort_connection(c);
            }
            if (n) {
                memcpy(c->output + c->pending, reply, (size_t)n);
                c->pending += (size_t)n;
                if (flush(c) != ERR_OK) { pbuf_free(p); return abort_connection(c); }
            }
            if (artiq_session_closing(c->state)) c->closing = 1;
        }
    }
    tcp_recved(c->pcb, p->tot_len);
    pbuf_free(p);
    return flush(c);
}
static err_t accepted(void *arg, struct tcp_pcb *pcb, err_t error) {
    (void)arg;
    if (error != ERR_OK) return error;
    for (size_t i = 0; i < 4; i++) {
        struct connection *c = &connections[i];
        if (!c->pcb) {
            c->pcb = pcb; c->pending = 0; c->closing = 0;
            artiq_session_init(c->state);
            callbacks(c);
            return ERR_OK;
        }
    }
    tcp_abort(pcb);
    return ERR_ABRT;
}
int genesys_management_start(const uint8_t *ip, size_t ip_len) {
    if (artiq_session_size() > sizeof(connections[0].state) || artiq_session_align() > 16) return -1;
    artiq_runtime_ready(ip, ip_len);
    struct tcp_pcb *pcb = tcp_new_ip_type(IPADDR_TYPE_V4);
    if (!pcb) return -1;
    if (tcp_bind(pcb, IP_ANY_TYPE, 1380) != ERR_OK) { tcp_close(pcb); return -1; }
    pcb = tcp_listen(pcb);
    if (!pcb) return -1;
    tcp_accept(pcb, accepted);
    xil_printf("GENESYS ARTIQ management transport ready @ port 1380; kernel/RPC pending\r\n");
    return 0;
}
