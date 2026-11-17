/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "master_leaf_codec.h"
int master_leaf_wire_test(void) {
 uint8_t b[1024];for(unsigned i=0;i<1024;i++)b[i]=0xa5;
 if(aux_master_leaf_encode(0x30,1,b,40)!=40)return 1;
 if(b[0]!=0x30||b[1]!=1||b[2]!=1||b[40]!=0xa5)return 2;
 for(unsigned i=3;i<34;i++)if(b[i])return 3;
 if(aux_master_leaf_encode(0x31,1,b,8)!=8||b[0]!=0x31||b[1]!=1)return 4;
 for(unsigned i=0;i<1024;i++)b[i]=0xa5;
 if(aux_master_leaf_encode(0x30,256,b,1024)!=-2)return 5;
 if(aux_master_leaf_encode(0x30,1,b,39)!=-4)return 6;
 for(unsigned i=0;i<1024;i++)if(b[i]!=0xa5)return 7;
 return 0;
}
