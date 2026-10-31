# SPDX-License-Identifier: LGPL-3.0-or-later
"""Standalone target object and stack/store inspection, no runtime link or HW."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
BASE=Path('/home/codex-hil/.local/state/artiq-builds');OUT=BASE/'pit-fault-record-audit-20261031-v1'
def main():
 OUT.mkdir(exist_ok=False)
 cmd=list(json.loads((BASE/'pit-irq-binding-audit-20261031-v1/build.json').read_text())['compile_commands'][0])
 source=ROOT/'diagnostics/ddr/pit_collect/pit_fault_record.c'
 cmd[cmd.index('-c')+1]=str(source);cmd[cmd.index('-o')+1]=str(OUT/'sha.o');cmd=[x for x in cmd if x not in ('-flto','-ffat-lto-objects')]
 subprocess.run(cmd,check=True,capture_output=True)
 tool=Path(cmd[0]).parent
 dis=subprocess.check_output([str(tool/'mb-objdump'),'-dr',str(OUT/'sha.o')],text=True)
 (HERE/'sha.dis').write_text(dis)
 bad=[line for line in dis.splitlines() if re.search(r'\b(sb|sbi|sh|shi|sbr|shr)\b',line)]
 if bad:raise ValueError('subword stores: '+str(bad))
 undefined=subprocess.check_output([str(tool/'mb-nm'),'-u',str(OUT/'sha.o')],text=True)
 if undefined.strip():raise ValueError('unreviewed external helper: '+undefined)
 su=(OUT/'sha.su').read_text();(HERE/'stack.txt').write_text(su)
 report=dict(status='STANDALONE_FAULT_RECORD_OBJECT_PASS_NOT_LINKED',hardware_executed=False,deployable=False,command=cmd,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),object_sha256=hashlib.sha256((OUT/'sha.o').read_bytes()).hexdigest(),undefined_symbols=undefined,subword_stores=bad,stack_usage=su,limits='Standalone non-LTO object only; no linked callback/pipeline, total stack/exception, physical acquisition, recovery or deployment qualification.')
 (HERE/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(su)
if __name__=='__main__':main()
