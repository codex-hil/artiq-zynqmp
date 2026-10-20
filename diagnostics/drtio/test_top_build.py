"""Synthetic build-validator controls, no implementation claims. LGPL-3.0-or-later."""
import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
CHECK=Path(__file__).with_name('check_top_build.py')

class TopBuildTests(unittest.TestCase):
    def fixture(self,root,lab):
        count,total=(9,202) if lab else (8,170)
        mapping=dict(magic=0x44525430,registers={'aux_tsc_load_count':{},'aux_tsc_snapshot_value':{}},dma={})
        # Nonempty DMA configuration is required to select DMA validation.
        mapping['dma']['arena']={}
        if lab:mapping['dma']['laboratory_read_delay']={'independent_metrics':True}
        groups=[dict(source='source'+str(i),first_stage='sink'+str(i),bits=32 if i==8 else 1) for i in range(count)]
        for n in ['top.bit','top.v','top.xdc']:(root/n).write_text('synthetic fixture only')
        (root/'csr-map.json').write_text(json.dumps(mapping))
        (root/'top_timing.rpt').write_text('All user specified timing constraints are met.')
        (root/'top_bus_skew.rpt').write_text('Slack (MET)\n'*(8+count))
        (root/'cdc-manifest.json').write_text(json.dumps({'dma_crossings':groups}))
        (root/'build.log').write_text('\n'.join('DMA_CDC_CHECK {source} {bits} {bits}'.format(**g) for g in groups))
        qualification=dict(status='PASS',groups=count,endpoints=total,sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ['csr-map.json','cdc-manifest.json']})
        (root/'dma-cdc-results.json').write_text(json.dumps(qualification))
    def run_check(self,p):return subprocess.run([sys.executable,str(CHECK),str(p),'--output',str(p/'results.json')],capture_output=True,text=True)
    def test_normal_and_lab_counts(self):
        for lab in [False,True]:
            with tempfile.TemporaryDirectory() as name:
                p=Path(name);self.fixture(p,lab);self.assertEqual(self.run_check(p).returncode,0)
    def test_missing_group_stale_hash_and_bad_skew(self):
        for case in ['group','hash','skew','endpoint']:
            with tempfile.TemporaryDirectory() as name:
                p=Path(name);self.fixture(p,True)
                self.assertEqual(self.run_check(p).returncode,0)
                if case=='group':
                    f=p/'cdc-manifest.json';d=json.loads(f.read_text());d['dma_crossings'].pop();f.write_text(json.dumps(d))
                if case=='hash':(p/'csr-map.json').write_text((p/'csr-map.json').read_text()+' ')
                if case=='skew':(p/'top_bus_skew.rpt').write_text('Slack (MET)\n'*16)
                if case=='endpoint':
                    f=p/'dma-cdc-results.json';d=json.loads(f.read_text());d['endpoints']=170;f.write_text(json.dumps(d))
                self.assertNotEqual(self.run_check(p).returncode,0,case)
                self.assertFalse((p/'results.json').exists())
