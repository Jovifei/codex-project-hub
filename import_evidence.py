"""Deterministic, append-only projection of an explicitly supplied evidence JSON.
No repository reads, model calls, owner updates or agent session operations.
"""
import argparse, copy, hashlib, json, os, subprocess, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
WORKTREE='coordination:five-project-receipts'
BRANCH='evidence-summary-only'
PREFIX='hub_evidence_v1:'
STATES={'recorded','blocked','unverified','passed_record','passed_verified','partial','not_received','historical','failed','unknown'}
def stamp(value):
 t=datetime.fromisoformat(value.replace('Z','+00:00'))
 if t.tzinfo is None: raise ValueError('timezone required')
 return t
def validate_snapshot(d):
 if d.get('schema')!='dashboard-evidence-snapshot-v1': raise ValueError('unsupported snapshot schema')
 stamp(d['checkedAt'])
 if not isinstance(d.get('notice'),str) or not isinstance(d.get('accessGaps'),list): raise ValueError('missing source context')
 ps=d.get('projects')
 if not isinstance(ps,list) or not ps or len({p['id'] for p in ps})!=len(ps): raise ValueError('invalid projects')
 for p in ps:
  if not isinstance(p.get('id'),str) or not __import__('re').fullmatch(r'[a-zA-Z0-9_.-]{1,200}',p['id']): raise ValueError('invalid evidence project id')
  for k in ('name','repository','goal','current','next'):
   if not isinstance(p.get(k),str) or not p[k].strip(): raise ValueError('invalid '+k)
  stamp(p['lastEngineeringAt'])
  if stamp(p['lastEngineeringAt'])>stamp(d['checkedAt']): raise ValueError('engineering time after check')
  if not isinstance(p.get('blockers'),list) or any(not isinstance(b,str) or not b for b in p['blockers']): raise ValueError('invalid blockers')
  stages=p.get('stages')
  if not isinstance(stages,list) or not stages or len(stages)>30 or len({s['id'] for s in stages})!=len(stages): raise ValueError('invalid stages')
  for s in stages:
   if s.get('status') not in STATES: raise ValueError('invalid evidence state')
   if any(not isinstance(s.get(k),str) or not s[k] for k in ('id','title','detail')): raise ValueError('invalid stage')
   if not isinstance(s.get('evidence'),list) or any(not isinstance(u,str) or not u.startswith('https://github.com/') for u in s['evidence']): raise ValueError('unsafe evidence URL')
  if len(artifact(d,p))>4000: raise ValueError('metadata exceeds contract string limit')
 return d
def artifact(d,p):
 return PREFIX+json.dumps({'version':1,'project_id':p['id'],'checkedAt':d['checkedAt'],'source':'用户提供的协调核对快照；仓库记录 / 他方回执 / 独立读取见阶段说明；本机导入器未重新验证','notice':d['notice'],'accessGaps':d['accessGaps'],'project':p},ensure_ascii=False,separators=(',',':'))
def union(new,old): return list(dict.fromkeys(new+old))
def metadata(status):
 for a in status.get('artifacts',[]):
  if a.startswith(PREFIX):
   try: return json.loads(a[len(PREFIX):])
   except ValueError: pass
 return None
def projected_phase_state(matches,allow_receipt=False):
 # The embedded compatibility view is a receipt, never an owner verification.
 if any(x['status'] in ('blocked','failed') for x in matches): return 'blocked'
 if any(x['status']=='partial' for x in matches): return 'partial'
 if not matches: return 'unknown'
 allowed={'passed_verified','passed_record'} if allow_receipt else {'passed_verified'}
 if all(x['status'] in allowed and x.get('evidence') for x in matches): return 'passed'
 if all(x['status'] in ('recorded','passed_record','passed_verified') for x in matches): return 'recorded'
 return 'pending'

def projection_current(p,old):
 prefixes=('最终可观察效果（管理摘要，未改Owner目标）：','可观察目标摘要（不得改Owner目标）：','当前阶段：','最近确认动作（来源分层）：','当前责任分工；最后有效用户决定 ','已验收与仅回执：','读取覆盖：')
 return union([p['current']],[x for x in old.get('current',[]) if not x.startswith(prefixes)])

def projection_next(p,old):
 return union([p['next']],[x for x in old.get('next',[]) if not x.startswith('下一阶段：')])

def build_event(d,p,s,event_id,reported_at):
 from core import validate
 old=s['status'] or {}
 prior=metadata(old)
 if prior and stamp(prior['checkedAt'])>stamp(d['checkedAt']): raise ValueError('older evidence cannot replace newer projection')
 arts=[a for a in old.get('artifacts',[]) if not a.startswith(PREFIX)]
 # Retain the compatible five-phase summary, updating only its evidence fields.
 for i,a in enumerate(arts):
  if a.startswith('hub_delivery_v1:'):
   m=json.loads(a.split(':',1)[1]); groups=[{'main','base','increment','baseline','remote','code','review','v2'}, {'ci'}, {'local','integrity'}, {'deploy','production','handoff','install'}, {'device','real','natural','acceptance'}]
   for index,(phase,ids) in enumerate(zip(m['phases'],groups)):
    matches=[x for x in p['stages'] if x['id'] in ids]
    phase['state']=projected_phase_state(matches,allow_receipt=index<2)
    phase['note']='；'.join(x['title']+'：'+x['detail'] for x in matches) or '此快照未提供该阶段证据'
    phase['evidence_at']=p['lastEngineeringAt']
   m.update(check_time=d['checkedAt'],last_actual_progress_at=p['lastEngineeringAt'],last_actual_progress=p['current'],evidence_links=union([u for st in p['stages'] for u in st['evidence']],[]))
   arts[i]='hub_delivery_v1:'+json.dumps(m,ensure_ascii=False,separators=(',',':'))
 e=dict(schema_version=1,kind='status',event_id=event_id,project_id=p['id'],agent_id='dashboard-evidence-importer',run_id='evidence-'+hashlib.sha256(d['checkedAt'].encode()).hexdigest()[:16],worktree_id=WORKTREE,branch=BRANCH,expected_revision=s['revision'],reported_at=reported_at,is_test=False,reported_status='blocked' if p['blockers'] else 'unknown',stage_id=old.get('stage_id','unknown'),current=projection_current(p,old),next=projection_next(p,old),blockers=union(p['blockers'],old.get('blockers',[])),versions=old.get('versions',[]),tests=old.get('tests',[]),artifacts=[artifact(d,p)]+arts,acceptance_claims=[])
 validate(e)
 if len(json.dumps(e,ensure_ascii=False).encode())>65536: raise ValueError('event exceeds 64KiB')
 return e
def fetch(url,path): return json.load(urllib.request.urlopen(url+path,timeout=10))
def event_lookup(url,pid,event_id):
 cursor=None
 for _ in range(1000):
  path='/api/history/'+pid+'?limit=100'+('&before='+str(cursor) if cursor else '')
  data=fetch(url,path)
  rows=data if isinstance(data,list) else data['events']
  found=next((x for x in rows if x['payload']['event_id']==event_id),None)
  if found:return found
  nxt=None if isinstance(data,list) else data.get('next_cursor')
  if nxt is None:return None
  if cursor is not None and nxt>=cursor:raise ValueError('history cursor did not advance')
  cursor=nxt
 raise ValueError('history lookup page limit exceeded; inspect locally')

def import_snapshot(d,url,retries=4):
 validate_snapshot(d)
 fingerprint=hashlib.sha256(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 def find(p):
  project=next((x for x in fetch(url,'/api/projects')['projects'] if x['project_id']==p['id']),None)
  if project is None: raise ValueError('unregistered evidence project: '+p['id'])
  return next(s for s in project['streams'] if s['worktree_id']==WORKTREE and s['branch']==BRANCH and not s['is_test'])
 # Validate every project against the latest registered stream before any write.
 at=datetime.now(timezone.utc).isoformat()
 for p in d['projects']:
  eid='evidence-'+fingerprint[:32]+'-'+p['id']
  if event_lookup(url,p['id'],eid) is None:
   build_event(d,p,find(p),eid,at)
 results=[]
 for p in d['projects']:
  eid='evidence-'+fingerprint[:32]+'-'+p['id']
  for attempt in range(retries):
   prior=event_lookup(url,p['id'],eid)
   if prior:
    results.append({**prior['result'],'project_id':p['id'],'duplicate':True}); break
   s=find(p)
   e=build_event(d,p,s,eid,datetime.now(timezone.utc).isoformat())
   proc=subprocess.run([sys.executable,str(ROOT/'report.py'),'--url',url,'send','-'],input=json.dumps(e,ensure_ascii=False),text=True,encoding='utf-8',capture_output=True,env={**os.environ,'PYTHONIOENCODING':'utf-8'})
   if proc.returncode==0:
    results.append(dict(project_id=p['id'],**json.loads(proc.stdout))); break
   if 'revision conflict' not in proc.stderr or attempt+1==retries: raise RuntimeError(proc.stderr.strip() or proc.stdout)
  else: raise RuntimeError('conflict retry limit exceeded')
 return results
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('snapshot',type=Path); ap.add_argument('--url',default='http://127.0.0.1:8765'); ap.add_argument('--check-only',action='store_true'); a=ap.parse_args()
 try:
  d=validate_snapshot(json.loads(a.snapshot.read_text(encoding='utf-8-sig')))
  if a.check_only: print(json.dumps({'valid':True,'projects':[p['id'] for p in d['projects']]},ensure_ascii=False))
  else: print(json.dumps(import_snapshot(d,a.url),ensure_ascii=False,indent=2))
 except (ValueError,KeyError,StopIteration,OSError,RuntimeError) as ex: print(str(ex),file=sys.stderr); sys.exit(1)
