"""Deterministic reporter: inspect revision, then post an immutable JSON event."""
import argparse,json,sys,urllib.request,urllib.error,uuid
from pathlib import Path
from core import now
p=argparse.ArgumentParser(); p.add_argument('--url',default='http://127.0.0.1:8765'); sub=p.add_subparsers(dest='command',required=True)
r=sub.add_parser('revision'); r.add_argument('project_id'); r.add_argument('--worktree',required=True); r.add_argument('--branch',required=True); r.add_argument('--test',action='store_true')
r=sub.add_parser('send'); r.add_argument('file',help='JSON event file or - for stdin')
r=sub.add_parser('template'); r.add_argument('project_id'); r.add_argument('--worktree',required=True); r.add_argument('--branch',required=True); r.add_argument('--agent',required=True); r.add_argument('--run',required=True); r.add_argument('--revision',type=int,required=True); r.add_argument('--test',action='store_true')
a=p.parse_args()
try:
 if a.command=='template':
  e={'schema_version':1,'kind':'status','event_id':str(uuid.uuid4()),'project_id':a.project_id,'agent_id':a.agent,'run_id':a.run,'worktree_id':a.worktree,'branch':a.branch,'expected_revision':a.revision,'reported_at':now(),'is_test':a.test,'reported_status':'unknown','stage_id':'unknown','current':[],'next':[],'blockers':[],'versions':[],'tests':[],'artifacts':[],'acceptance_claims':[]}; print(json.dumps(e,ensure_ascii=False,indent=2))
 elif a.command=='revision':
  d=json.load(urllib.request.urlopen(a.url+'/api/projects',timeout=5)); project=next((x for x in d['projects'] if x['project_id']==a.project_id),None)
  if project is None: raise ValueError('unregistered project')
  s=next((x for x in project['streams'] if x['worktree_id']==a.worktree and x['branch']==a.branch and x['is_test']==a.test),None); print(json.dumps({'revision':s['revision'] if s else 0,'definition':s['definition'] if s else {k:project[k] for k in ('goal','route','acceptance')}},ensure_ascii=False))
 else:
  raw=sys.stdin.buffer.read() if a.file=='-' else Path(a.file).read_bytes(); e=json.loads(raw.decode('utf-8-sig')); req=urllib.request.Request(a.url+'/api/events',data=json.dumps(e).encode(),headers={'Content-Type':'application/json'},method='POST'); print(urllib.request.urlopen(req,timeout=10).read().decode())
except urllib.error.HTTPError as ex: print(ex.read().decode(),file=sys.stderr); sys.exit(2)
except (OSError,ValueError) as ex: print(str(ex),file=sys.stderr); sys.exit(1)
