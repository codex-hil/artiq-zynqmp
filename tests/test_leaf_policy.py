"""Execute actual readiness policy, including every unavailable state; LGPL-3.0-or-later."""
import subprocess,tempfile,unittest
from pathlib import Path
class LeafPolicyTests(unittest.TestCase):
 def test_all_readiness_gates(self):
  h=Path(__file__).resolve().parents[1]/'diagnostics/drtio/aux_protocol'
  source='''#include <assert.h>
#include "leaf_policy.h"
int main(void){
 assert(leaf_ready(1,1,1,1,0,1,0,0));
 assert(!leaf_ready(0,1,1,1,0,1,0,0));
 assert(!leaf_ready(2,1,1,1,0,1,0,0));
 assert(!leaf_ready(1,0,1,1,0,1,0,0));
 assert(!leaf_ready(1,1,0,1,0,1,0,0));
 assert(!leaf_ready(1,1,1,0,0,1,0,0));
 assert(!leaf_ready(1,1,1,1,1,1,0,0));
 assert(!leaf_ready(1,1,1,1,0,0,0,0));
 assert(!leaf_ready(1,1,1,1,0,1,1,0));
 assert(!leaf_ready(1,1,1,1,0,1,0,1));return 0;}
'''
  with tempfile.TemporaryDirectory() as tmp:
   c=Path(tmp)/'test.c';c.write_text(source);exe=Path(tmp)/'test'
   subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-I'+str(h),str(c),'-o',str(exe)],check=True,timeout=30)
   subprocess.run([str(exe)],check=True,timeout=5)
