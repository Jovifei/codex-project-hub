import json,unittest
from pathlib import Path

class RegistrationChecklistTests(unittest.TestCase):
 def test_checklist_covers_catalog_and_stays_unconfirmed(self):
  catalog=json.loads(Path('docs/PROJECT_CATALOG_20261025.json').read_text(encoding='utf-8'))
  text=Path('docs/REGISTRATION_CHECKLIST_20261025.md').read_text(encoding='utf-8')
  self.assertIn('不自动导入',text)
  self.assertIn('待用户确认',text)
  for p in catalog['projects']:
   self.assertIn(p['id'],text,msg=p['id'])
   self.assertIn(p['repository'],text,msg=p['id'])

if __name__=='__main__':unittest.main()
