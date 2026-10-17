"""Execute actual context method under success/failure; LGPL-3.0-or-later."""
import ast,hashlib,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import artiq.coredevice.dma as dma
from prepare_dma_cursor_overlay import prepare,validate


def invoke(source,failure):
    tree=ast.parse(source)
    context=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='DMARecordContextManager')
    method=next(n for n in context.body if isinstance(n,ast.FunctionDef) and n.name=='__exit__')
    method.decorator_list=[]
    cursor=[123];calls=[]
    def stop(duration,enabled):
        calls.append((duration,enabled))
        if failure:raise failure
    def restore(value):cursor[0]=value
    scope=dict(dma_record_stop=stop,now_mu=lambda:cursor[0],at_mu=restore)
    module=ast.Module(body=[method],type_ignores=[])
    exec(compile(ast.fix_missing_locations(module),'context-under-test','exec'),scope)
    caught=None
    try:scope['__exit__'](SimpleNamespace(saved_now_mu=456,enable_ddma=True))
    except RuntimeError as error:caught=error
    return cursor[0],calls,caught

class CursorTests(unittest.TestCase):
    def test_actual_method_restores_and_propagates_same_exception(self):
        source=Path(dma.__file__).resolve().parent.parent
        original=(source/'coredevice/dma.py').read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            overlay=Path(tmp)/'overlay';prepare(source,overlay)
            validate(overlay)
            changed=(overlay/'artiq/coredevice/dma.py').read_text()
            error=RuntimeError('upload refused')
            self.assertEqual(invoke(original.decode(),error)[0],123) # negative control
            self.assertEqual(invoke(changed,None),(456,[(123,True)],None))
            cursor,calls,caught=invoke(changed,error)
            self.assertEqual(cursor,456);self.assertEqual(calls,[(123,True)])
            self.assertIs(caught,error)
            self.assertEqual((source/'coredevice/dma.py').read_bytes(),original)
            with self.assertRaises(ValueError):prepare(source,overlay)
            (overlay/'artiq/coredevice/dma.py').write_text(changed+'\n# changed\n')
            with self.assertRaises(ValueError):validate(overlay)

if __name__=='__main__':unittest.main()
