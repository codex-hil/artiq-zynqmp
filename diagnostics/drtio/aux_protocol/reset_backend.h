/* Hardware-confirmed queue reset; preserves PHY state and TSC.
 * LGPL-3.0-or-later. Included after MMIO/wait helpers. */
#pragma once
static int reset_backend_ready(void) {
 return !rd(REG_AUX_IN_RESET) && rd(REG_AUX_RX_UP) &&
        !rd(REG_AUX_RT_REPLY_FAULT) && !rd(REG_AUX_PHY_RESET_REQUEST) &&
        !rd(REG_AUX_PHY_RESET_APPLIED);
}
static int reset_backend(void) {
 uint32_t loads=rd(REG_AUX_TSC_LOAD_COUNT);
 if(!reset_backend_ready() || rd(REG_AUX_RTIO_RESET_REQUEST) ||
    rd(REG_AUX_RTIO_RESET_APPLIED))return -1;
 wr(REG_AUX_RTIO_RESET_REQUEST,1);
 if(wait(REG_AUX_RTIO_RESET_APPLIED,1))return -1;
 usleep(100); /* upstream satman minimum hold */
 if(!reset_backend_ready())return -1;
 wr(REG_AUX_RTIO_RESET_REQUEST,0);
 if(wait(REG_AUX_RTIO_RESET_APPLIED,0) || !reset_backend_ready() ||
    rd(REG_AUX_RTIO_ERROR_FLAGS) || rd(REG_AUX_TSC_LOAD_COUNT)!=loads)return -1;
 return 0;
}
static int release_backend(void) {
 if(wait(REG_AUX_RTIO_RESET_APPLIED,1) ||
    wait(REG_AUX_PHY_RESET_APPLIED,1))return -1;
 wr(REG_AUX_PHY_RESET_REQUEST,0);
 if(wait(REG_AUX_PHY_RESET_APPLIED,0))return -1;
 wr(REG_AUX_RTIO_RESET_REQUEST,0);
 return wait(REG_AUX_RTIO_RESET_APPLIED,0) || !reset_backend_ready() ? -1:0;
}
