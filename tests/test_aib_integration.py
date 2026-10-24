"""Full offline preflight and actual child dispatch branch. LGPL-3.0-or-later."""
import ast,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from test_candidate_runtime_hw import preflight,observer_preflight
MANIFEST=ROOT/'evidence/aib-guard-integration-2026-10-24/inputs.json'
class Tests(unittest.TestCase):
 def test_full_preflight_and_bad_opt_in(self):
  files=preflight(json.loads((ROOT/'evidence/trained-observer-integration-2026-10-22/runtime-inputs.json').read_text()))
  observer_preflight(MANIFEST,files)
  with tempfile.TemporaryDirectory() as tmp:
   for value in ['true',1]:
    m=json.loads(MANIFEST.read_text());m['aib_observation']=value;p=Path(tmp)/'bad.json';p.write_text(json.dumps(m))
    with self.assertRaises(ValueError):observer_preflight(p,files)
   m=json.loads(MANIFEST.read_text());del m['script_sha256']['scripts/probe_aib_state.tcl'];p.write_text(json.dumps(m))
   with self.assertRaises(ValueError):observer_preflight(p,files)
 def test_actual_dispatch_retains_failure(self):
  tree=ast.parse((ROOT/'scripts/run_trained_observer.py').read_text())
  branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.Attribute) and n.test.attr=='aib_observation')
  calls=[]
  def xs(*args):calls.append(args);raise RuntimeError('transport timeout')
  with self.assertRaises(RuntimeError):
   exec(compile(ast.Module(body=branch.body,type_ignores=[]),'<actual-aib-branch>','exec'),{'a':SimpleNamespace(server='offline'),'result':{},'xs':xs})
  self.assertEqual(calls,[('aib-after-guard','probe_aib_state.tcl','offline','210383B7F02DA')])
if __name__=='__main__':unittest.main()
