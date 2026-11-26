#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Generate a hash-gated disabled-by-default GEM hook in a NEW source copy."""
import argparse,difflib,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--expected-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
data=a.source.read_bytes();digest=hashlib.sha256(data).hexdigest();assert digest==a.expected_sha256,'Retained source changed; refuse patch'
a.output.mkdir(parents=True,exist_ok=False);text=data.decode()
include='#include "lwipopts.h"\n';entry='void emacps_error_handler(void *arg,u8 Direction, u32 ErrorWord)\n{\n'
assert text.count(include)==1 and text.count(entry)==1
switch='#if defined(MNF_ENABLE_COPY_ONLY_GEM_HOOK) && MNF_ENABLE_COPY_ONLY_GEM_HOOK\n'
modified=text.replace(include,include+switch+'#include "network_fault_gem_copy_hook.h"\n#endif\n',1).replace(entry,entry+switch+'\tmnf_copy_gem_fault_publish(ErrorWord);\n#endif\n',1)
(a.output/'xemacpsif_hw.c').write_text(modified)
(a.output/'hook.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True),modified.splitlines(True),fromfile='retained/xemacpsif_hw.c',tofile='copy-only/xemacpsif_hw.c')))
(a.output/'receipt.json').write_text(json.dumps({'status':'COPY_ONLY_HOOK_PREPARED_DISABLED_BY_DEFAULT','source':str(a.source),'source_sha256':digest,'copy_sha256':hashlib.sha256(modified.encode()).hexdigest(),'hardware_accessed':False,'deployed_sources_changed':False},indent=2)+'\n')
assert a.source.read_bytes()==data;print('COPY_ONLY_GEM_HOOK_PREPARED')
