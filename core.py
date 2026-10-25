"""Local project ledger. No model, shell or project file access."""
import json, sqlite3, hashlib, re, os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('HUB_DATA_DIR',str(ROOT/'data')))/'hub.sqlite3'
def now(): return datetime.now(timezone.utc).isoformat()
class Fault(Exception):
 def __init__(self,message,code=400): super().__init__(message); self.code=code
@contextmanager
def connect(db=DB):
 c=sqlite3.connect(db,timeout=15); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON')
 try:
  with c: yield c
 finally: c.close()
def initialize(db=DB):
 Path(db).parent.mkdir(parents=True,exist_ok=True)
 with connect(db) as c:
  c.executescript('''
  PRAGMA journal_mode=WAL;
  CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, baseline TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0);
  CREATE TABLE IF NOT EXISTS streams(project_id TEXT NOT NULL REFERENCES projects(id),worktree_id TEXT NOT NULL,branch TEXT NOT NULL,is_test INTEGER NOT NULL,revision INTEGER NOT NULL,snapshot TEXT NOT NULL,PRIMARY KEY(project_id,worktree_id,branch,is_test));
  CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY,hash TEXT NOT NULL,payload TEXT NOT NULL,received_at TEXT NOT NULL,result TEXT NOT NULL);
  CREATE TRIGGER IF NOT EXISTS immutable_event_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append only'); END;
  CREATE TRIGGER IF NOT EXISTS immutable_event_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append only'); END;
  ''')
  from catalog import ensure
  ensure(c)
def register(projects,db=DB):
 with connect(db) as c:
  for p in projects: c.execute('INSERT OR IGNORE INTO projects(id,baseline) VALUES(?,?)',(p['project_id'],json.dumps(p,ensure_ascii=False)))
def string(v,name,limit=4000):
 if not isinstance(v,str) or not v.strip() or len(v)>limit: raise Fault('invalid '+name)
 return v
def strings(v,name):
 if not isinstance(v,list) or len(v)>100: raise Fault('invalid '+name)
 for s in v: string(s,name)
def stamp(v,name):
 string(v,name,80)
 try:
  t=datetime.fromisoformat(v.replace('Z','+00:00'))
  if t.tzinfo is None: raise ValueError()
  if t.timestamp()>datetime.now(timezone.utc).timestamp()+300: raise ValueError()
 except ValueError: raise Fault('invalid timestamp '+name)
 return t
COMMON={'schema_version','event_id','project_id','agent_id','run_id','worktree_id','branch','expected_revision','reported_at','is_test','kind'}
FIELDS={'status':{'reported_status','current','next','blockers','stage_id','versions','tests','artifacts','acceptance_claims'},'definition':{'goal','acceptance','route'},'verification':{'acceptance_id','outcome','evidence_refs','reviewer','note','verified_at'}}
def validate(e):
 if not isinstance(e,dict): raise Fault('JSON object required')
 if e.get('schema_version')!=1 or type(e.get('schema_version')) is not int: raise Fault('schema_version must be 1')
 kind=e.get('kind'); allowed=FIELDS.get(kind)
 if allowed is None or set(e)!=COMMON|allowed: raise Fault('missing or unknown fields; see contract.json')
 for k in ('event_id','project_id','agent_id','run_id','worktree_id','branch'): string(e[k],k,200)
 if not re.fullmatch(r'[a-zA-Z0-9_.-]+',e['project_id']): raise Fault('invalid project_id')
 if type(e['expected_revision']) is not int or e['expected_revision']<0: raise Fault('invalid expected_revision')
 if type(e['is_test']) is not bool: raise Fault('is_test must be boolean')
 stamp(e['reported_at'],'reported_at')
 if kind=='status':
  if e['reported_status'] not in ('unknown','active','blocked','paused','claimed_complete'): raise Fault('invalid reported_status')
  for k in ('current','next','blockers','versions','tests','artifacts','acceptance_claims'): strings(e[k],k)
  string(e['stage_id'],'stage_id',200)
 elif kind=='definition':
  string(e['goal'],'goal'); items(e['acceptance'],'acceptance',{'id','text'}); items(e['route'],'route',{'id','name','detail'})
 else:
  string(e['acceptance_id'],'acceptance_id',200)
  if e['outcome'] not in ('verified','reopened'): raise Fault('invalid outcome')
  strings(e['evidence_refs'],'evidence_refs'); string(e['reviewer'],'reviewer',200); string(e['note'],'note')
  if not e['evidence_refs']: raise Fault('verification requires references')
  stamp(e['verified_at'],'verified_at')
def items(v,name,fields):
 if not isinstance(v,list) or not v or len(v)>100: raise Fault('invalid '+name)
 ids=[]
 for x in v:
  if not isinstance(x,dict) or set(x)!=fields: raise Fault('invalid '+name+' item')
  for k in fields: string(x[k],name+'.'+k)
  ids.append(x['id'])
 if len(ids)!=len(set(ids)): raise Fault('duplicate '+name+' id')
def submit(e,db=DB,owner=False):
 validate(e)
 if e['kind']!='status' and not owner: raise Fault('definition / verification are owner CLI only',403)
 canonical=json.dumps(e,sort_keys=True,separators=(',',':'),ensure_ascii=False); digest=hashlib.sha256(canonical.encode()).hexdigest()
 with connect(db) as c:
  c.execute('BEGIN IMMEDIATE')
  old=c.execute('SELECT hash,result FROM events WHERE event_id=?',(e['event_id'],)).fetchone()
  if old:
   if old['hash']!=digest: raise Fault('event_id reused with different content',409)
   return {**json.loads(old['result']),'duplicate':True}
  p=c.execute('SELECT * FROM projects WHERE id=?',(e['project_id'],)).fetchone()
  if not p: raise Fault('unregistered project',404)
  from catalog import state as catalog_state,key as catalog_key
  if catalog_state(c,e['project_id'],'project').get('archived') or catalog_state(c,e['project_id'],catalog_key('stream',e['worktree_id'],e['branch'],e['is_test'])).get('archived'): raise Fault('project or stream archived; restore before reporting',409)
  key=(e['project_id'],e['worktree_id'],e['branch'],int(e['is_test']))
  stream=c.execute('SELECT * FROM streams WHERE project_id=? AND worktree_id=? AND branch=? AND is_test=?',key).fetchone()
  baseline=json.loads(p['baseline'])
  s=json.loads(stream['snapshot']) if stream else {'definition':{k:baseline[k] for k in ('goal','acceptance','route')},'definition_revision':p['revision'],'verification':{},'status':None,'revision':0}
  if e['expected_revision']!=s['revision']: raise Fault('revision conflict; current_revision='+str(s['revision']),409)
  received=now(); kind=e['kind']
  if kind=='status':
   if e['stage_id'] not in {x['id'] for x in s['definition']['route']}|{'unknown'}: raise Fault('unknown stage_id')
   if not set(e['acceptance_claims'])<={x['id'] for x in s['definition']['acceptance']}: raise Fault('unknown acceptance id')
   if s['status'] and stamp(e['reported_at'],'reported_at')<stamp(s['status']['reported_at'],'reported_at'): raise Fault('older report would overwrite current status',409)
   s['status']={k:e[k] for k in COMMON|FIELDS['status']}; s['status']['received_at']=received
   # Any new report invalidates previous verification until explicitly reviewed again.
   for v in s['verification'].values(): v['outcome']='needs_review'
  elif kind=='definition':
   s['definition']={k:e[k] for k in FIELDS['definition']}; s['definition_revision']+=1; s['verification']={}; s['status']=None
  else:
   if not s['status']: raise Fault('no reported status to review')
   if e['acceptance_id'] not in {a['id'] for a in s['definition']['acceptance']}: raise Fault('unknown acceptance id')
   s['verification'][e['acceptance_id']]={k:e[k] for k in FIELDS['verification']}; s['verification'][e['acceptance_id']]['reviewed_status_revision']=s['status_revision']
  s['revision']+=1
  if kind=='status': s['status_revision']=s['revision']
  s['received_at']=received; s['last_event_id']=e['event_id']; s['worktree_id']=e['worktree_id']; s['branch']=e['branch']; s['is_test']=e['is_test']
  result={'event_id':e['event_id'],'revision':s['revision'],'received_at':received,'duplicate':False}
  c.execute('INSERT INTO streams VALUES(?,?,?,?,?,?) ON CONFLICT(project_id,worktree_id,branch,is_test) DO UPDATE SET revision=excluded.revision,snapshot=excluded.snapshot',key+(s['revision'],json.dumps(s,ensure_ascii=False)))
  c.execute('INSERT INTO events VALUES(?,?,?,?,?)',(e['event_id'],digest,canonical,received,json.dumps(result)))
  return result
def overview(db=DB,include_archived=False):
 with connect(db) as c:
  projects=[]
  for row in c.execute('SELECT * FROM projects ORDER BY rowid'):
   from catalog import state,provenance,key
   p=json.loads(row['baseline']);meta=state(c,row['id'],'project')
   if meta.get('archived') and not include_archived:continue
   p['catalog_revision']=meta['revision'];p['archived']=meta.get('archived',False);p['goal_provenance']=provenance(c,row['id'],'project',{f:p[f] for f in ('goal','acceptance','route')})
   if p['goal_provenance']['status']=='unconfirmed':p['goal_provenance'].update(source_ref=p.get('goal_source_ref'),version=p.get('goal_source_version'))
   p['streams']=[]
   for r in c.execute('SELECT snapshot FROM streams WHERE project_id=? ORDER BY worktree_id,branch,is_test',(row['id'],)):
    s=json.loads(r['snapshot']);k=key('stream',s['worktree_id'],s['branch'],s['is_test']);sm=state(c,row['id'],k)
    if sm.get('archived') and not include_archived:continue
    s['archived']=sm.get('archived',False);s['catalog_revision']=sm['revision'];s['goal_provenance']=provenance(c,row['id'],k,s['definition']);p['streams'].append(s)
   projects.append(p)
  return {'schema_version':1,'server_time':now(),'projects':projects}
def history(pid,db=DB):
 with connect(db) as c:
  return [{'payload':json.loads(r['payload']),'received_at':r['received_at'],'result':json.loads(r['result'])} for r in c.execute('SELECT * FROM events WHERE json_extract(payload,\'$.project_id\')=? ORDER BY rowid DESC',(pid,))]

def history_page(pid,db=DB,limit=50,before=None,stream=None):
 if type(limit) is not int or not 1<=limit<=100:raise Fault('limit must be 1..100')
 if before is not None and (type(before) is not int or before<1):raise Fault('invalid history cursor')
 where="json_extract(payload,'$.project_id')=?";args=[pid]
 if before is not None:where+=' and rowid<?';args.append(before)
 if stream is not None:
  if not isinstance(stream,list) or len(stream)!=3 or type(stream[2]) is not bool:raise Fault('invalid stream filter')
  for v in stream[:2]:string(v,'stream',200)
  where+=" and json_extract(payload,'$.worktree_id')=? and json_extract(payload,'$.branch')=? and json_extract(payload,'$.is_test')=?";args+=stream
 with connect(db) as c:
  rows=c.execute('select rowid,* from events where '+where+' order by rowid desc limit ?',args+[limit+1]).fetchall()
  return {'events':[{'payload':json.loads(r['payload']),'received_at':r['received_at'],'result':json.loads(r['result'])} for r in rows[:limit]],'next_cursor':rows[limit-1]['rowid'] if len(rows)>limit else None}
