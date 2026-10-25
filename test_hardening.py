import copy,json,tempfile,unittest
from pathlib import Path
import core

class CatalogTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=Path(self.tmp.name)/'hub.sqlite3';core.initialize(self.db)
  self.p=json.loads(Path('seed.json').read_text(encoding='utf-8'))[0];core.register([self.p],self.db)
 def tearDown(self):self.tmp.cleanup()
 def op(self,**changes):
  e=dict(schema_version=1,event_id='catalog-one',action='update',project_id=self.p['project_id'],scope='project',expected_revision=0,actor='test-owner',reason='Synthetic test',data={'name':'Renamed example'})
  e.update(changes);return e
 def apply(self,e):
  from catalog import apply
  return apply(e,self.db)
 def test_catalog_cas_and_duplicate(self):
  e=self.op();r=self.apply(e);self.assertEqual(r['revision'],1);self.assertTrue(self.apply(e)['duplicate'])
  with self.assertRaises(core.Fault):self.apply(self.op(event_id='conflict'))
 def test_archive_restore_preserves_history(self):
  self.apply(self.op(action='archive',data={}));self.assertEqual(core.overview(self.db)['projects'],[])
  self.assertEqual(len(core.overview(self.db,include_archived=True)['projects']),1)
  self.apply(self.op(event_id='restore',action='restore',expected_revision=1,data={}))
  self.assertEqual(len(core.overview(self.db)['projects']),1)
  with core.connect(self.db) as c:
   self.assertEqual(c.execute('select count(*) from catalog_events').fetchone()[0],2)
   import sqlite3
   with self.assertRaises(sqlite3.IntegrityError):c.execute('delete from catalog_events')
 def test_goal_confirmation_requires_evidence_and_matches_definition(self):
  from catalog import definition_hash
  bad=self.op(action='confirm_goal',data={})
  with self.assertRaises(core.Fault):self.apply(bad)
  d={k:self.p[k] for k in ('goal','acceptance','route')}
  data={'definition_hash':definition_hash(d),'source_ref':'synthetic source','version':'test-v1','approved_by':'test-owner','approved_at':core.now(),'evidence_refs':['synthetic owner approval']}
  self.apply(self.op(action='confirm_goal',data=data))
  p=core.overview(self.db)['projects'][0];self.assertEqual(p['goal_provenance']['status'],'confirmed')
  self.assertEqual(p['goal_provenance']['definition_hash'],definition_hash(d))
 def test_new_project_and_update_cannot_silently_change_goal(self):
  p=copy.deepcopy(self.p);p['project_id']='custom-project';p['number']=10
  self.apply(self.op(project_id='custom-project',action='create',data=p))
  with self.assertRaises(core.Fault):self.apply(self.op(event_id='bad',data={'goal':'silent overwrite'}))
  self.assertEqual(len(core.overview(self.db)['projects']),2)
 def test_schema_supports_registered_custom_ids(self):
  schema=json.loads(Path('contract.json').read_text())
  for variant in schema['oneOf']:
   self.assertNotIn('enum',variant['properties']['project_id'])
   self.assertIn('pattern',variant['properties']['project_id'])
 def test_history_pagination(self):
  from test_core import LedgerTest
  t=LedgerTest();t.p=self.p
  for i in range(4):core.submit(t.event(event_id=f'e-{i}',expected_revision=i),self.db)
  first=core.history_page(self.p['project_id'],self.db,limit=2)
  second=core.history_page(self.p['project_id'],self.db,limit=2,before=first['next_cursor'])
  self.assertEqual(len(first['events']),2);self.assertEqual(len(second['events']),2)
  self.assertFalse({e['payload']['event_id'] for e in first['events']}&{e['payload']['event_id'] for e in second['events']})
  self.assertIsNone(second['next_cursor'])
  with self.assertRaises(core.Fault):core.history_page(self.p['project_id'],self.db,limit=0)

if __name__=='__main__':unittest.main()
