import unittest,tempfile,json,threading,urllib.request,urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from core import initialize,register,submit,overview,history,Fault,now,connect

class LedgerTest(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.db=Path(self.temp.name)/'test.sqlite3';initialize(self.db);self.p=json.loads(Path(__file__).with_name('seed.json').read_text(encoding='utf-8'))[0];register([self.p],self.db)
 def tearDown(self): self.temp.cleanup()
 def event(self,**changes):
  e={'schema_version':1,'kind':'status','event_id':'test-1','project_id':self.p['project_id'],'agent_id':'test-agent','run_id':'run-1','worktree_id':'test-worktree','branch':'test-branch','expected_revision':0,'reported_at':now(),'is_test':True,'reported_status':'active','stage_id':'s1','current':['TEST ONLY: ledger check'],'next':[],'blockers':[],'versions':['synthetic-v1'],'tests':['synthetic, no project tests run'],'artifacts':['evidence/test-report.json'],'acceptance_claims':['a1']};e.update(changes);return e
 def test_idempotent_retry_after_restart(self):
  e=self.event();a=submit(e,self.db);initialize(self.db);b=submit(e,self.db);self.assertEqual(a['revision'],b['revision']);self.assertTrue(b['duplicate']);self.assertEqual(len(history(self.p['project_id'],self.db)),1)
 def test_conflict_preserves_last_valid_snapshot(self):
  submit(self.event(),self.db)
  with self.assertRaises(Fault) as f:submit(self.event(event_id='test-2'),self.db)
  self.assertEqual(f.exception.code,409);self.assertEqual(overview(self.db)['projects'][0]['streams'][0]['revision'],1)
 def test_event_id_collision(self):
  e=self.event();submit(e,self.db)
  with self.assertRaises(Fault):submit({**e,'current':['changed']},self.db)
 def test_worktree_branch_and_test_isolation(self):
  submit(self.event(),self.db);submit(self.event(event_id='b',branch='other'),self.db);submit(self.event(event_id='c',worktree_id='other'),self.db);submit(self.event(event_id='d',is_test=False),self.db);self.assertEqual(len(overview(self.db)['projects'][0]['streams']),4)
 def test_schema_unknown_and_goal_in_status_rejected(self):
  for changes in ({'goal':'silently change'},{'expected_revision':True},{'reported_status':'done'},{'schema_version':2},{'current':'not list'},{'stage_id':'no-such-stage'},{'acceptance_claims':['missing']},{'reported_at':'2026-01-01'}):
   with self.subTest(changes=changes),self.assertRaises(Fault):submit(self.event(**changes),self.db)
  self.assertEqual(history(self.p['project_id'],self.db),[])
 def test_unregistered_project(self):
  with self.assertRaises(Fault):submit(self.event(project_id='not-registered'),self.db)
 def verification(self,revision=1,outcome='verified',eid='v1'):
  base={k:v for k,v in self.event().items() if k in {'schema_version','project_id','agent_id','run_id','worktree_id','branch','reported_at','is_test'}}
  return {**base,'kind':'verification','event_id':eid,'expected_revision':revision,'acceptance_id':'a1','outcome':outcome,'evidence_refs':['synthetic-evidence'],'reviewer':'test reviewer','note':'TEST: not real evidence','verified_at':now()}
 def test_claim_verify_reopen_and_new_report_invalidates(self):
  submit(self.event(),self.db);v=self.verification()
  with self.assertRaises(Fault):submit(v,self.db)
  submit(v,self.db,owner=True);self.assertEqual(overview(self.db)['projects'][0]['streams'][0]['verification']['a1']['outcome'],'verified')
  submit(self.verification(2,'reopened','v2'),self.db,owner=True);self.assertEqual(overview(self.db)['projects'][0]['streams'][0]['verification']['a1']['outcome'],'reopened')
  submit(self.verification(3,'verified','v3'),self.db,owner=True);submit(self.event(event_id='new',expected_revision=4),self.db);self.assertEqual(overview(self.db)['projects'][0]['streams'][0]['verification']['a1']['outcome'],'needs_review')
 def test_definition_separate_and_scoped(self):
  e=self.event();d={k:v for k,v in e.items() if k in {'schema_version','event_id','project_id','agent_id','run_id','worktree_id','branch','expected_revision','reported_at','is_test'}};d.update(kind='definition',goal='Explicit test goal',acceptance=[{'id':'new-a','text':'test criterion'}],route=[{'id':'new-s','name':'test stage','detail':'test detail'}])
  with self.assertRaises(Fault):submit(d,self.db)
  submit(d,self.db,owner=True);self.assertEqual(overview(self.db)['projects'][0]['goal'],self.p['goal']);self.assertEqual(overview(self.db)['projects'][0]['streams'][0]['definition']['goal'],'Explicit test goal')
 def test_concurrent_writers_one_wins(self):
  def write(n):
   try:submit(self.event(event_id='race-'+str(n)),self.db);return True
   except Fault:return False
  with ThreadPoolExecutor(max_workers=6) as pool: results=list(pool.map(write,range(6)))
  self.assertEqual(sum(results),1);self.assertEqual(len(history(self.p['project_id'],self.db)),1)
 def test_append_only(self):
  submit(self.event(),self.db)
  with connect(self.db) as c:
   import sqlite3
   with self.assertRaises(sqlite3.IntegrityError): c.execute('DELETE FROM events')
 def test_old_report_rejected(self):
  submit(self.event(),self.db)
  with self.assertRaises(Fault):submit(self.event(event_id='old',expected_revision=1,reported_at='2020-01-01T00:00:00Z'),self.db)

class HTTPTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from server import Handler,ThreadingHTTPServer
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.url=f'http://127.0.0.1:{cls.server.server_port}'
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
 def code(self,path='/',method='GET',headers=None,body=None):
  try:
   with urllib.request.urlopen(urllib.request.Request(self.url+path,method=method,headers=headers or {},data=body),timeout=3) as r:return r.status
  except urllib.error.HTTPError as e:
   code=e.code;e.close();return code
 def test_host_dns_rebinding_rejected(self): self.assertEqual(self.code(headers={'Host':'evil.example'}),403)
 def test_cross_site_write_rejected(self): self.assertEqual(self.code('/api/events','POST',{'Origin':'https://evil.example','Content-Type':'application/json'},b'{}'),403)
 def test_simple_form_write_rejected(self): self.assertEqual(self.code('/api/events','POST',{'Content-Type':'text/plain'},b'{}'),415)
 def test_preflight_not_supported(self): self.assertEqual(self.code('/api/events','OPTIONS'),501)
 def test_arbitrary_file_routes_rejected(self):
  for path in ('/core.py','/data/hub.sqlite3','/art/../seed.json','/api/shell','/api/read?path=E:/private'): self.assertEqual(self.code(path),404)
if __name__=='__main__':unittest.main(verbosity=2)
