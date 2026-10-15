"""Compile and execute the firmware's actual C gate; LGPL-3.0-or-later."""
from pathlib import Path
import subprocess
import tempfile
import unittest


class TSCAckPolicyTests(unittest.TestCase):
    def test_actual_header_reset_stale_gap_and_fault_controls(self):
        header=Path(__file__).resolve().parents[1]/'diagnostics/drtio/aux_protocol'
        source=r'''
#include <assert.h>
#include "tsc_ack_policy.h"
int main(void) {
 struct tsc_ack_state s={0,0};
 assert(tsc_ack_step(&s,0,0,1,0)==0);
 assert(tsc_ack_step(&s,1,0,0,0)==0); /* not ready never ACKs */
 assert(tsc_ack_step(&s,0,0,1,0)==0);
 assert(tsc_ack_step(&s,1,0,1,0)==1);
 assert(tsc_ack_step(&s,1,0,1,0)==0); /* no stale replay */
 assert(tsc_ack_step(&s,1,0,0,0)==0);
 assert(tsc_ack_step(&s,1,0,1,0)==0); /* readiness loss is not a reset */
 assert(tsc_ack_step(&s,2,0,1,0)==1);
 assert(tsc_ack_step(&s,4,0,1,0)==-1); /* gap is fatal */
 assert(tsc_ack_step(&s,3,0,1,0)==0);
 assert(tsc_ack_step(&s,0,1,0,0)==0);
 assert(tsc_ack_step(&s,1,0,1,1)==-1); /* hardware fault */
 assert(tsc_ack_step(&s,1,0,1,0)==0); /* fault stays blocked */
 assert(tsc_ack_step(&s,0,1,0,0)==0);
 assert(tsc_ack_step(&s,1,0,1,0)==1); /* fresh reset epoch */
 return 0;
}'''
        with tempfile.TemporaryDirectory() as tmp:
            c=Path(tmp)/'test.c';c.write_text(source)
            exe=Path(tmp)/'test'
            subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-I'+str(header),str(c),'-o',str(exe)],check=True,timeout=30)
            subprocess.run([str(exe)],check=True,timeout=5)
