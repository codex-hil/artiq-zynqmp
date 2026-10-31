# SPDX-License-Identifier: LGPL-3.0-or-later
"""Small standalone audit compilation; never links/deploys a runtime."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=Path('/home/codex-hil/.local/state/artiq-builds')
OUT=BASE/'pit-irq-callback-audit-20261031-v1'
def main():
 OUT.mkdir(exist_ok=False)
 prior=json.loads((BASE/'pmu-ro-context-audit-20261028/build.json').read_text())
 cmd=list(prior['compile_commands'][0]);source=ROOT/'diagnostics/ddr/pit_collect/pit_irq_audit.c'
 cmd[cmd.index('-c')+1]=str(source);cmd[cmd.index('-o')+1]=str(OUT/'pit_irq_audit.o')
 cmd=[x for x in cmd if x not in ('-flto','-ffat-lto-objects')]+['-DARTIQ_PIT_IRQ_AUDIT_ONLY=1']
 subprocess.run(cmd,check=True,capture_output=True,text=True)
 tool=Path(cmd[0]).parent
 dis=subprocess.check_output([str(tool/'mb-objdump'),'-dr',str(OUT/'pit_irq_audit.o')],text=True)
 (HERE/'callbacks.dis').write_text(dis)
 sys.path.insert(0,str(ROOT/'scripts'))
 from review_pmu_irq_policy import review
 helper=review(Path('/srv/codex-hil-data/artiq-zynqmp/build-vivado/fsbl-spd-dump-20261022'),OUT/'helpers')
 (HERE/'interrupt-helper.dis').write_text((OUT/'helpers/microblaze_disable_interrupts.dis').read_text())
 report=dict(hardware_executed=False,deployable=False,status='STANDALONE_COMPILE_NOT_LINKED',command=cmd,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),header_sha256=hashlib.sha256((source.with_suffix('.h')).read_bytes()).hexdigest(),object_sha256=hashlib.sha256((OUT/'pit_irq_audit.o').read_bytes()).hexdigest(),helper=helper,limits='Standalone non-LTO callbacks and separately compiled helper only; no linked runtime binding, physical MSR, exception exclusion or deployment.')
 (HERE/'build.json').write_text(json.dumps(report,indent=2)+'\n')
 print(report['status'])
if __name__=='__main__':main()
