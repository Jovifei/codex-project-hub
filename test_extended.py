import copy,json,tempfile,unittest
from pathlib import Path
import core
from catalog import apply,definition_hash
import test_core as core_tests
import test_hardening as hardening_tests

class ExtendedTests(unittest.TestCase):
 setUp=hardening_tests.CatalogTests.setUp
 tearDown=hardening_tests.CatalogTests.tearDown
 op=hardening_tests.CatalogTests.op
 def event(self,**changes):
  t=core_tests.LedgerTest();t.p=self.p;return t.event(**changes)
 def test_stream_archive_blocks_new_reports_not_retries(self):
  e=self.event();core.submit(e,self.db)
  a=self.op(scope='stream',worktree_id=e['worktree_id'],branch=e['branch'],is_test=True,action='archive',data={})
  apply(a,self.db);self.assertTrue(core.submit(e,self.db)['duplicate'])
  with self.assertRaises(core.Fault):core.submit(self.event(event_id='new',expected_revision=1),self.db)
  apply({**a,'event_id':'restore','action':'restore','expected_revision':1},self.db)
  core.submit(self.event(event_id='new',expected_revision=1),self.db)
  self.assertEqual(len(core.history(self.p['project_id'],self.db)),2)
 def test_stream_confirmation_invalidated_by_definition(self):
  e=self.event();core.submit(e,self.db);d={k:self.p[k] for k in ('goal','route','acceptance')}
  a=self.op(scope='stream',worktree_id=e['worktree_id'],branch=e['branch'],is_test=True,action='confirm_goal',data={'definition_hash':definition_hash(d),'source_ref':'test','version':'1','approved_by':'test-owner','approved_at':core.now(),'evidence_refs':['synthetic']})
  apply(a,self.db);self.assertEqual(core.overview(self.db)['projects'][0]['streams'][0]['goal_provenance']['status'],'confirmed')
  payload={k:e[k] for k in core.COMMON};payload.update(kind='definition',event_id='new-definition',expected_revision=1,**d);payload['goal']='Revised synthetic goal';core.submit(payload,self.db,owner=True)
  self.assertEqual(core.overview(self.db)['projects'][0]['streams'][0]['goal_provenance']['status'],'unconfirmed')
 def test_status_exchange_preview_and_apply(self):
  from transfer import import_status
  path=Path(self.tmp.name)/'exchange.json';path.write_text(json.dumps({'schema':'hub-status-exchange-v1','events':[self.event()]}),encoding='utf-8')
  self.assertTrue(import_status(path,self.db)['preview']);self.assertEqual(core.history(self.p['project_id'],self.db),[])
  self.assertFalse(import_status(path,self.db,True)['preview']);self.assertTrue(import_status(path,self.db,True)['results'][0]['duplicate'])
 def test_history_stream_filter(self):
  e=self.event();core.submit(e,self.db);core.submit(self.event(event_id='other',branch='another'),self.db)
  page=core.history_page(self.p['project_id'],self.db,stream=[e['worktree_id'],e['branch'],True]);self.assertEqual([r['payload']['event_id'] for r in page['events']],['test-1'])
 def test_catalog_edit_audit_keeps_previous_metadata(self):
  from catalog import history
  apply(self.op(),self.db)
  audit=history(self.p['project_id'],self.db)['events'][0]['audit']
  self.assertEqual(audit['previous_baseline']['name'],self.p['name'])
 def test_candidate_source_does_not_confirm_goal(self):
  apply(self.op(data={'goal_status':'README candidate','goal_source_ref':'synthetic README','goal_source_version':'synthetic version'}),self.db)
  g=core.overview(self.db)['projects'][0]['goal_provenance'];self.assertEqual(g['status'],'unconfirmed');self.assertEqual(g['source_ref'],'synthetic README');self.assertIsNone(g['approved_by'])

if __name__=='__main__':unittest.main()
