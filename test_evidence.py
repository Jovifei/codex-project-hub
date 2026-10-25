import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import import_evidence as ie

class EvidenceTests(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((Path(__file__).parent/'tests/fixtures/evidence.json').read_text(encoding='utf-8'))
  self.s={'revision':7,'status':{'current':['用户保留记录'],'next':['用户下一步'],'blockers':['用户卡点'],'versions':['user-version'],'tests':['user-test'],'artifacts':['user-artifact'],'stage_id':'unknown'}}
 def test_valid_size_and_preserve_fields(self):
  ie.validate_snapshot(self.d)
  for p in self.d['projects']:
   e=ie.build_event(self.d,p,self.s,'test-event','2026-10-11T08:00:00+00:00')
   self.assertNotIn('goal',e);self.assertEqual(e['expected_revision'],7);self.assertIn('用户保留记录',e['current']);self.assertEqual(e['versions'],['user-version']);self.assertIn('user-artifact',e['artifacts']);self.assertTrue(all(len(a)<=4000 for a in e['artifacts']))
 def test_malformed_and_unsafe(self):
  for mutate in [lambda d:d.update(schema='wrong'),lambda d:d['projects'][0]['stages'][0].update(status='fake'),lambda d:d['projects'][0]['stages'][0].update(evidence=['javascript:alert(1)']),lambda d:d['projects'][0].update(lastEngineeringAt='2030-01-01T00:00:00+00:00')]:
   d=copy.deepcopy(self.d);mutate(d)
   with self.assertRaises(ValueError):ie.validate_snapshot(d)
 def test_custom_registered_id_format_and_paged_duplicate_lookup(self):
  d=copy.deepcopy(self.d);d['projects'][0]['id']='custom-project';ie.validate_snapshot(d)
  e=ie.build_event(d,d['projects'][0],self.s,'custom-event','2026-10-11T08:00:00Z');self.assertEqual(e['project_id'],'custom-project')
  pages=[{'events':[],'next_cursor':50},{'events':[{'payload':{'event_id':'old-event'}}],'next_cursor':None}]
  with patch.object(ie,'fetch',side_effect=pages) as f:
   self.assertEqual(ie.event_lookup('http://test','custom-project','old-event')['payload']['event_id'],'old-event');self.assertIn('before=50',f.call_args[0][1])
 def test_old_projection_rejected(self):
  s=copy.deepcopy(self.s);s['status']['artifacts']=[ie.PREFIX+json.dumps({'checkedAt':'2026-10-12T00:00:00+08:00'})]
  with self.assertRaises(ValueError):ie.build_event(self.d,self.d['projects'][0],s,'event','2026-10-11T08:00:00+00:00')
 def projection(self,status,evidence=None,stage_id='acceptance'):
  d=copy.deepcopy(self.d);p=d['projects'][0];p['stages']=[{'id':stage_id,'title':'Synthetic stage','status':status,'detail':'Synthetic claim','evidence':evidence or []}]
  s=copy.deepcopy(self.s);s['status']['artifacts']=['hub_delivery_v1:'+json.dumps({'version':1,'project_id':'example-1','phases':[{'state':'unknown'} for _ in range(5)]})]
  e=ie.build_event(d,p,s,'projection-test','2026-10-11T08:00:00Z')
  return json.loads(next(a for a in e['artifacts'] if a.startswith('hub_delivery_v1:')).split(':',1)[1]),e
 def test_recorded_never_becomes_passed(self):
  for stage_id,index in [('code',0),('ci',1),('local',2),('deploy',3),('acceptance',4)]:
   with self.subTest(stage_id=stage_id):
    m,e=self.projection('recorded',stage_id=stage_id);self.assertNotEqual(m['phases'][index]['state'],'passed');self.assertEqual(e['acceptance_claims'],[])
 def test_claimed_receipt_cannot_pass_real_acceptance(self):
  for status,evidence,expected in [('passed_record',['https://github.com/example/example/pull/1'],'recorded'),('passed_verified',[],'recorded'),('passed_verified',['https://github.com/example/example/pull/1'],'passed')]:
   m,e=self.projection(status,evidence);self.assertEqual(m['phases'][4]['state'],expected);self.assertEqual(e['acceptance_claims'],[])
  m,_=self.projection('passed_record',['https://github.com/example/example/actions/runs/1'],stage_id='ci');self.assertEqual(m['phases'][1]['state'],'passed')
 def test_new_projection_drops_only_old_management_summary_lines(self):
  s=copy.deepcopy(self.s);s['status']['current']+=['当前阶段：OLD PHASE','最终可观察效果（管理摘要，未改Owner目标）：OLD GOAL'];s['status']['next']+=['下一阶段：OLD NEXT']
  old=copy.deepcopy(s);e=ie.build_event(self.d,self.d['projects'][0],s,'projection','2026-10-11T08:00:00Z')
  self.assertFalse(any('OLD PHASE' in x or 'OLD GOAL' in x for x in e['current']));self.assertFalse(any('OLD NEXT' in x for x in e['next']));self.assertIn('用户保留记录',e['current']);self.assertIn('用户下一步',e['next']);self.assertEqual(s,old)
 def test_registered_ids_are_never_implicitly_aliased(self):
  import tempfile,core
  with tempfile.TemporaryDirectory() as tmp:
   db=Path(tmp)/'identity.sqlite3';core.initialize(db)
   baseline=json.loads(Path('seed.json').read_text(encoding='utf-8'))[0];other=copy.deepcopy(baseline);other['project_id']='etf';core.register([baseline,other],db)
   d=copy.deepcopy(self.d);p=d['projects'][0];p['id']='etf';s=copy.deepcopy(self.s);s['revision']=0
   e=ie.build_event(d,p,s,'identity','2026-10-11T08:00:00Z');self.assertEqual(e['project_id'],'etf');core.submit(e,db)
   records={p['project_id']:p for p in core.overview(db)['projects']};self.assertEqual(len(records['etf']['streams']),1);self.assertEqual(records['example-1']['streams'],[])
   p['id']='not-registered';bad=ie.build_event(d,p,s,'unknown','2026-10-11T08:00:00Z')
   with self.assertRaises(core.Fault) as f:core.submit(bad,db)
   self.assertEqual(f.exception.code,404)
 def test_unknown_import_target_rejected_before_send(self):
  d=copy.deepcopy(self.d);d['projects'][0]['id']='not-registered'
  def fetch(url,path):return [] if path.startswith('/api/history') else {'projects':[{'project_id':'etf','streams':[]},{'project_id':'example-1','streams':[]}]}
  with patch.object(ie,'fetch',fetch),patch.object(ie.subprocess,'run') as send:
   with self.assertRaisesRegex(ValueError,'unregistered evidence project'):ie.import_snapshot(d,'http://test')
   send.assert_not_called()
 def test_revision_conflict_merge_and_duplicate(self):
  d=copy.deepcopy(self.d);d['projects']=d['projects'][:1];pid=d['projects'][0]['id'];s=copy.deepcopy(self.s);s.update(worktree_id=ie.WORKTREE,branch=ie.BRANCH,is_test=False);events=[];attempts=[]
  def fetch(url,path):return events if path.startswith('/api/history') else {'projects':[{'project_id':pid,'streams':[s]}]}
  def send(args,**kw):
   e=json.loads(kw['input']);attempts.append(e)
   if len(attempts)==1:
    s['revision']+=1;s['status']['current'].append('并发用户记录')
    return SimpleNamespace(returncode=2,stderr='revision conflict; current_revision=8',stdout='')
   self.assertEqual(e['expected_revision'],8);self.assertIn('并发用户记录',e['current']);events.append({'payload':e,'result':{'event_id':e['event_id'],'revision':9,'received_at':'now','duplicate':False}})
   return SimpleNamespace(returncode=0,stdout=json.dumps(events[-1]['result']),stderr='')
  with patch.object(ie,'fetch',fetch),patch.object(ie.subprocess,'run',send):
   result=ie.import_snapshot(d,'http://test');self.assertEqual(result[0]['revision'],9)
   s['status']['artifacts']=[ie.PREFIX+json.dumps({'checkedAt':'2026-10-12T00:00:00+08:00'})]
   again=ie.import_snapshot(d,'http://test');self.assertTrue(again[0]['duplicate']);self.assertEqual(len(attempts),2)
if __name__=='__main__':unittest.main()
