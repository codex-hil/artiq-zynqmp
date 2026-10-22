"""Static inventory rejects incomplete configuration; LGPL-3.0-or-later."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_ddr_masters import PORTS,parameters


def fixture():
 root=ET.Element('SYSTEM');m=ET.SubElement(root,'MODULE',MODTYPE='zynq_ultra_ps_e')
 m=ET.SubElement(m,'PARAMETERS')
 for name in PORTS:ET.SubElement(m,'PARAMETER',NAME=name,VALUE='1' if name.endswith('S_AXI_GP2') else '0')
 return root,m


class InventoryTests(unittest.TestCase):
 def test_explicit_enabled_slave_port(self):
  root,_=fixture();r=parameters(ET.tostring(root))
  self.assertEqual(r['PSU__USE__S_AXI_GP2'],'1');self.assertEqual(r['PSU__USE__GDMA'],'0')
 def test_missing_duplicate_nonboolean_rejected(self):
  for kind in ['missing','duplicate','value','missing-value']:
   root,m=fixture()
   if kind=='missing':m.remove(m[0])
   elif kind=='duplicate':ET.SubElement(m,'PARAMETER',NAME=PORTS[0],VALUE='0')
   elif kind=='value':m[0].set('VALUE','false')
   else:del m[0].attrib['VALUE']
   with self.assertRaises(ValueError):parameters(ET.tostring(root))
 def test_bus_interface_parameter_is_not_ps_config(self):
  root,_=fixture();module=root.find('MODULE')
  bus=ET.SubElement(module,'BUSINTERFACES');nested=ET.SubElement(bus,'PARAMETERS')
  ET.SubElement(nested,'PARAMETER',NAME=PORTS[0],VALUE='bad')
  self.assertEqual(parameters(ET.tostring(root))[PORTS[0]],'0')
 def test_multiple_ps_modules_rejected(self):
  root,_=fixture();ET.SubElement(root,'MODULE',MODTYPE='zynq_ultra_ps_e')
  with self.assertRaises(ValueError):parameters(ET.tostring(root))


if __name__=='__main__':unittest.main()
