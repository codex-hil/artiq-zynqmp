"""Package generated Trenz reference RTL for a fresh remote build; no hardware."""
import argparse,hashlib,json,re,shutil
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
source=Path(__file__).resolve().parents[1]/'gateware'
rtl=source/'fabric_jesd_tx.v'
if not rtl.is_file():raise SystemExit('Run make hdl first')
memories=set(re.findall(r'\$readmemh\("([^"\n]+)"',rtl.read_text()))
files=['fabric_jesd_tx.v','spi-console.v','fabric-clock-constraints.tcl','build-slow6144.tcl']+sorted(memories)
for name in files:
 if Path(name).name!=name or not (source/name).is_file():raise SystemExit(f'Invalid/missing generated input: {name}')
args.output.mkdir(parents=True,exist_ok=False)
for name in files:shutil.copy2(source/name,args.output/name)
(args.output/'build.tcl').write_text('source [file join [file dirname [file normalize [info script]]] build-slow6144.tcl]\n')
manifest={'target':'TRENZ_REFERENCE_NOT_AXAU15','sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.iterdir() if p.is_file()}}
(args.output/'inputs.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'{len(files)} source inputs packaged in {args.output}; target is Trenz reference only')
