/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Reproduce in directory with current aux_protocol headers and test_master_setup_cooperative.c copied as test.c. gcc -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=undefined mutation-driver.c -o test */
/* Test-only codec stubs; cancellation ownership only, no wire claims. */
#include "test.c"
int32_t aux_master_star_path_encode(uint32_t d,uint8_t *b,size_t n){(void)d;for(size_t i=0;i<n;i++)b[i]=0;return 40;}
int32_t aux_master_leaf_encode(uint32_t k,uint32_t v,uint8_t *b,size_t n){(void)k;(void)v;for(size_t i=0;i<n;i++)b[i]=0;return 8;}
int32_t aux_master_routing_ack_decode(const uint8_t *b,size_t n){(void)b;(void)n;return 0x32;}
int32_t aux_master_control_encode(uint32_t k,uint32_t v,uint8_t *b,size_t n){(void)k;(void)v;for(size_t i=0;i<n;i++)b[i]=0;return 8;}
int32_t aux_master_control_decode(const uint8_t *b,size_t n){(void)b;(void)n;return 1;}
int main(void){cancellation_callback_test();return 0;}
