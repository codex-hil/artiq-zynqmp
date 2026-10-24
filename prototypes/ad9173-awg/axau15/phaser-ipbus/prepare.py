"""Generate a self-contained Vivado input directory; build only on Dell."""
import argparse,hashlib,json,subprocess,sys,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();out=a.output.resolve()
if out.exists():raise SystemExit('Use a fresh output directory')
here=Path(__file__).resolve().parent;base=here.parent/'jesd-probe'
subprocess.run([sys.executable,str(here/'generate.py'),'--output',str(out)],check=True)
for name in ['core.v','constraints.tcl','spi_gpio.v','status_scan.v']:shutil.copy2(base/name,out/name)
for name in ['eth_scan.v','synth.tcl','implement.tcl']:shutil.copy2(here/name,out/name)
shutil.copytree(here/'vendor/ipbus',out/'ipbus');shutil.copy2(here/'vendor/ipbus-order.txt',out/'ipbus-order.txt')
(out/'build.tcl').write_text('source synth.tcl\nclose_design\nsource implement.tcl\n')
manifest={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()}
(out/'inputs-sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(out)
