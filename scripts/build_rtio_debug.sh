#!/usr/bin/env bash
# Reuse a verified PS DMA export; build a separate analyzer/moninj PL image.
set -euo pipefail
if [ "$#" -ne 2 ] && { [ "$#" -ne 3 ] || [ "$3" != --generate-only ]; }; then
 echo 'Usage: PS_DMA_EXPORT FRESH_OUTPUT [--generate-only]' >&2; exit 2
fi
threads=${VIVADO_THREADS:-2}
case "$threads" in 1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16) ;; *) echo 'VIVADO_THREADS must be 1..16' >&2; exit 2;; esac
export VIVADO_THREADS="$threads"
repo=$(cd "$(dirname "$0")/.." && pwd)
ps=$(realpath "$1");out=$(realpath -m "$2")
[ ! -e "$out" ] || { echo 'Use a fresh output directory' >&2; exit 2; }
mkdir -p "$out"
artiq=${ARTIQ_SOURCE:-$repo/common/artiq}
migen=${MIGEN_SOURCE:-$repo/common/migen}
misoc=${MISOC_SOURCE:-/srv/codex-hil-data/artiq-zynqmp/reference/misoc-current}
litex=${LITEX_SOURCE:-/srv/codex-hil-data/artiq-zynqmp/reference/litex}
for dependency in "$artiq/artiq" "$migen/migen" "$misoc/misoc" "$litex/litex"; do
 [ -d "$dependency" ] || { echo "Missing explicit source dependency: $dependency" >&2; exit 2; }
done
export PYTHONPATH="$artiq:$migen:$misoc:$litex:$repo/diagnostics/drtio:$repo/boards/genesys_zu-5ev/1_gateware${PYTHONPATH:+:$PYTHONPATH}"
py=${PYTHON:-/srv/codex-hil-data/artiq-zynqmp/venv/bin/python}
cd "$out"
"$py" - "$ps" "$out" <<'PY'
from pathlib import Path
import sys,re,json,hashlib,subprocess,importlib,os
from diag_gateware import DiagnosticPlatform
from gateware import Top
p=DiagnosticPlatform(Path(sys.argv[1]));top=Top(p,'local-rtio-dma',True)
p.build(top,build_dir=sys.argv[2],run=False)
top.local_rtio.write_map(Path(sys.argv[2])/'csr-map.json')
out=Path(sys.argv[2]);s=(out/'top_route.tcl').read_text()
name='platform_zynq_ultra_ps_e_0_0'
s=s.replace(f'synth_ip [get_ips {name}] -force',f'create_ip_run [get_ips {name}]\nlaunch_runs {name}_synth_1 -jobs 2\nwait_on_run {name}_synth_1\nif {{[get_property PROGRESS [get_runs {name}_synth_1]] ne "100%"}} {{error "PS synthesis failed"}}')
count=0
for line in (out/'top.v').read_text().splitlines():
 if 'mr_ff = "true"' in line:
  m=re.search(r'reg \[(\d+):(\d+)\]',line);count+=int(m[1])-int(m[2])+1 if m else 1
fix=f'''set first_sync [get_cells -hierarchical -filter {{mr_ff == TRUE && REF_NAME =~ FD*}}]
if {{[llength $first_sync] != {count}}} {{error "Unexpected CDC register count"}}
set_false_path -to [get_pins -of_objects $first_sync -filter {{REF_PIN_NAME == D}}]
'''
needle='report_timing_summary -file top_timing_synth.rpt'
assert needle in s
s=s.replace(needle,fix+needle)
(out/'top_route.tcl').write_text('set_param general.maxThreads '+os.environ['VIVADO_THREADS']+'\n'+s)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def source(module):
 item=importlib.import_module(module);path=Path(item.__file__).resolve()
 result=dict(module=module,path=str(path),sha256=sha(path))
 try:
  root=subprocess.check_output(['git','-C',str(path.parent),'rev-parse','--show-toplevel'],text=True,stderr=subprocess.DEVNULL).strip()
  result.update(git_root=root,commit=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip(),tracked_patch_sha256=hashlib.sha256(subprocess.check_output(['git','-C',root,'diff','--binary','HEAD','--'])).hexdigest())
 except subprocess.CalledProcessError:result['git']='not available; module file hash only'
 return result
files=[out/n for n in ('top.v','top.xdc','top.tcl','top_route.tcl','top_bitstream.tcl','csr-map.json')]+sorted(out.glob('*.init'))+sorted((out/'ip').rglob('*.xci'))
record=dict(status='HDL_GENERATED_NOT_SYNTHESIZED',hardware_executed=False,python=sys.version,
 max_threads=int(os.environ['VIVADO_THREADS']),cdc_first_stage_registers=count,
 dependencies=[source(n) for n in ('gateware','diag_gateware','migen','artiq','misoc','litex')],
 ps_ip_sources={str(path):sha(Path(path)) for path in p.ips},
 files=[dict(path=str(path.relative_to(out)),sha256=sha(path)) for path in files])
(out/'generation.json').write_text(json.dumps(record,indent=2)+'\n')
PY
if [ "${3:-}" = --generate-only ]; then echo "HDL generated; Vivado not invoked: $out"; exit 0; fi
cd "$out"
vivado -mode batch -source top.tcl > build.log 2>&1
"$py" - <<'PY'
from pathlib import Path
import hashlib,json
assert 'All user specified timing constraints are met.' in Path('top_timing.rpt').read_text()
files=['top.bit','top.v','top.xdc','csr-map.json','top_timing.rpt']
r={'kind':'build-not-hardware','status':'PASS','scope':'local RTIO CoreDMA plus BRAM analyzer and MonInj','sha256':{f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files}}
Path('results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
PY
