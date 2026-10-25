"""Owner-only catalog ledger. Archive is reversible; no business files are touched."""
import json,hashlib,re
from core import connect,Fault,string,strings,stamp,items,now,DB

def ensure(c):
 c.executescript('''
 CREATE TABLE IF NOT EXISTS catalog_state(project_id TEXT NOT NULL,scope_key TEXT NOT NULL,revision INTEGER NOT NULL,snapshot TEXT NOT NULL,PRIMARY KEY(project_id,scope_key));
 CREATE TABLE IF NOT EXISTS catalog_events(event_id TEXT PRIMARY KEY,hash TEXT NOT NULL,payload TEXT NOT NULL,received_at TEXT NOT NULL,result TEXT NOT NULL,audit TEXT NOT NULL DEFAULT '{}');
 CREATE TRIGGER IF NOT EXISTS immutable_catalog_update BEFORE UPDATE ON catalog_events BEGIN SELECT RAISE(ABORT,'append only'); END;
 CREATE TRIGGER IF NOT EXISTS immutable_catalog_delete BEFORE DELETE ON catalog_events BEGIN SELECT RAISE(ABORT,'append only'); END;
 ''')
 if 'audit' not in {r[1] for r in c.execute('pragma table_info(catalog_events)')}:c.execute("alter table catalog_events add column audit TEXT NOT NULL DEFAULT '{}'")

def definition_hash(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def key(scope,worktree=None,branch=None,is_test=None):
 if scope=='project':return 'project'
 if scope!='stream':raise Fault('scope must be project or stream')
 string(worktree,'worktree_id',200);string(branch,'branch',200)
 if type(is_test) is not bool:raise Fault('is_test must be boolean')
 return json.dumps([worktree,branch,is_test],separators=(',',':'))

def state(c,pid,k):
 r=c.execute('select * from catalog_state where project_id=? and scope_key=?',(pid,k)).fetchone()
 return json.loads(r['snapshot']) if r else {'revision':0,'archived':False}

def provenance(c,pid,k,d):
 s=state(c,pid,k);approval=s.get('goal_provenance')
 if approval and approval['definition_hash']==definition_hash(d):return {'status':'confirmed',**approval}
 return {'status':'unconfirmed','definition_hash':definition_hash(d),'source_ref':None,'version':None,'approved_by':None,'approved_at':None,'evidence_refs':[]}

META={'name','category','root','art','canonical_repository','aliases','goal_status','goal_source_ref','goal_source_version'}
def validate_metadata(d):
 if set(d)-META:raise Fault('unknown metadata field; goals require separate definition event')
 for k,v in d.items():
  if k=='aliases':
   strings(v,k)
   if len(v)!=len(set(v)):raise Fault('duplicate aliases')
  else:string(v,k)
 if 'canonical_repository' in d and not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',d['canonical_repository']):raise Fault('repository must be owner/name')
 if 'art' in d and not re.fullmatch(r'/art/[1-9]\.svg',d['art']):raise Fault('art must be a bundled SVG')

def validate_project(p):
 required={'project_id','number','name','category','root','art','goal','acceptance','route'}
 if not isinstance(p,dict) or not required<=set(p) or set(p)-required-META:raise Fault('invalid project baseline')
 if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,200}',p['project_id']):raise Fault('invalid project_id')
 if type(p['number']) is not int or p['number']<1:raise Fault('invalid number')
 validate_metadata({k:v for k,v in p.items() if k in META})
 string(p['goal'],'goal');items(p['acceptance'],'acceptance',{'id','text'});items(p['route'],'route',{'id','name','detail'})

def apply(e,db=DB):
 required={'schema_version','event_id','action','project_id','scope','expected_revision','actor','reason','data'}
 if not isinstance(e,dict) or set(e)-required-{'worktree_id','branch','is_test'} or not required<=set(e):raise Fault('invalid catalog envelope')
 if type(e['schema_version']) is not int or e['schema_version']!=1:raise Fault('unsupported catalog version')
 for f in ('event_id','project_id','actor','reason'):string(e[f],f,200 if f!='reason' else 4000)
 if not re.fullmatch(r'[a-zA-Z0-9_.-]+',e['project_id']):raise Fault('invalid project_id')
 if type(e['expected_revision']) is not int or e['expected_revision']<0:raise Fault('invalid catalog revision')
 if e['scope']=='project' and set(e)&{'worktree_id','branch','is_test'}:raise Fault('project scope cannot contain stream identity')
 k=key(e['scope'],e.get('worktree_id'),e.get('branch'),e.get('is_test'))
 if not isinstance(e['data'],dict):raise Fault('catalog data object required')
 action=e['action'];pid=e['project_id'];d=e['data'];canonical=json.dumps(e,sort_keys=True,separators=(',',':'),ensure_ascii=False);h=hashlib.sha256(canonical.encode()).hexdigest()
 with connect(db) as c:
  c.execute('BEGIN IMMEDIATE')
  prev=c.execute('select hash,result from catalog_events where event_id=?',(e['event_id'],)).fetchone()
  if prev:
   if prev['hash']!=h:raise Fault('catalog event_id collision',409)
   return {**json.loads(prev['result']),'duplicate':True}
  s=state(c,pid,k)
  if e['expected_revision']!=s['revision']:raise Fault('catalog revision conflict',409)
  row=c.execute('select baseline from projects where id=?',(pid,)).fetchone()
  audit={'previous_catalog_state':json.loads(json.dumps(s)),'previous_baseline':json.loads(row['baseline']) if row else None}
  if action=='create':
   if row or k!='project':raise Fault('project exists or invalid create scope',409)
   validate_project(d)
   if d['project_id']!=pid:raise Fault('project identity mismatch')
   c.execute('insert into projects(id,baseline) values(?,?)',(pid,json.dumps(d,ensure_ascii=False)))
  else:
   if not row:raise Fault('unregistered project',404)
   baseline=json.loads(row['baseline'])
   stream=None
   if k!='project':
    r=c.execute('select snapshot from streams where project_id=? and worktree_id=? and branch=? and is_test=?',(pid,e['worktree_id'],e['branch'],int(e['is_test']))).fetchone()
    if not r:raise Fault('unregistered stream',404)
    stream=json.loads(r['snapshot'])
   if action=='update':
    if k!='project':raise Fault('stream identity cannot be edited')
    validate_metadata(d);baseline.update(d);c.execute('update projects set baseline=? where id=?',(json.dumps(baseline,ensure_ascii=False),pid))
   elif action in ('archive','restore'):
    if d:raise Fault('archive data must be empty')
    s['archived']=action=='archive'
   elif action=='confirm_goal':
    fields={'definition_hash','source_ref','version','approved_by','approved_at','evidence_refs'}
    if set(d)!=fields:raise Fault('explicit source, version and approval evidence required')
    for f in fields-{'evidence_refs'}:string(d[f],f)
    strings(d['evidence_refs'],'evidence_refs');stamp(d['approved_at'],'approved_at')
    if not d['evidence_refs'] or d['approved_by']!=e['actor']:raise Fault('owner approval identity/evidence required')
    definition=stream['definition'] if stream else {f:baseline[f] for f in ('goal','acceptance','route')}
    if d['definition_hash']!=definition_hash(definition):raise Fault('definition changed; review again',409)
    s['goal_provenance']=d
   else:raise Fault('unsupported catalog action')
  s['revision']+=1;s['last_event_id']=e['event_id'];s['received_at']=now()
  result={'event_id':e['event_id'],'revision':s['revision'],'received_at':s['received_at'],'duplicate':False}
  c.execute('insert into catalog_state values(?,?,?,?) on conflict(project_id,scope_key) do update set revision=excluded.revision,snapshot=excluded.snapshot',(pid,k,s['revision'],json.dumps(s,ensure_ascii=False)))
  c.execute('insert into catalog_events(event_id,hash,payload,received_at,result,audit) values(?,?,?,?,?,?)',(e['event_id'],h,canonical,s['received_at'],json.dumps(result),json.dumps(audit,ensure_ascii=False)))
  return result

def export_catalog(db=DB):
 from core import overview
 data=overview(db,include_archived=True)
 return {'schema':'hub-catalog-v1','exported_at':now(),'projects':[{k:v for k,v in p.items() if k not in ('streams','goal_provenance')} for p in data['projects']], 'notice':'Contains project metadata; review/redact before sharing. No status events included.'}

def history(pid,db=DB,limit=50,before=None):
 if type(limit) is not int or not 1<=limit<=100:raise Fault('limit must be 1..100')
 if before is not None and (type(before) is not int or before<1):raise Fault('invalid catalog cursor')
 with connect(db) as c:
  where="json_extract(payload,'$.project_id')=?";args=[pid]
  if before is not None:where+=' and rowid<?';args.append(before)
  rows=c.execute('select rowid,* from catalog_events where '+where+' order by rowid desc limit ?',args+[limit+1]).fetchall()
  return {'events':[{'payload':json.loads(r['payload']),'result':json.loads(r['result']),'audit':json.loads(r['audit']),'received_at':r['received_at']} for r in rows[:limit]],'next_cursor':rows[limit-1]['rowid'] if len(rows)>limit else None}
