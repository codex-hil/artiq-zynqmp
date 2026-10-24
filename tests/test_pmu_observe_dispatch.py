"""Execute actual request-only branch without a guard. LGPL-3.0-or-later."""
import ast,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_observe_transport_keeps_legacy_arity_without_guard(self):
  tree=ast.parse((ROOT/'scripts/run_trained_observer.py').read_text())
  branches=[n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='request' and any(isinstance(c,ast.Call) and isinstance(c.func,ast.Name) and c.func.id=='request_parse' for c in ast.walk(n))]
  self.assertEqual(len(branches),1);calls=[]
  def xs(*args):
   self.assertEqual(args[:4],('pmu-request','probe_pmu_observe_request.tcl','offline','210383B7F02DA'))
   self.assertEqual(len(args),6);calls.append(args);return 'record'
  def parse(text,nonce):
   self.assertEqual(text,'record');self.assertGreater(nonce,0);return {'status':'mock'}
  env={'request':{'elf':{'sha256':'pinned'}},'guard':None,'a':SimpleNamespace(pmu_request_inputs='manifest',server='offline'),'REPO':ROOT,'request_preflight':lambda *a:None,'xs':xs,'request_parse':parse,'result':{}}
  exec(compile(ast.Module(body=branches[0].body,type_ignores=[]),'<actual-request-branch>','exec'),env)
  self.assertEqual(len(calls),1);self.assertEqual(env['result']['pmu_request'],{'status':'mock'})
if __name__=='__main__':unittest.main()
