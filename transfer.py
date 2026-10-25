"""Explicit local-only status exchange. Preview by default; never rewrites revisions."""
import argparse,json,sqlite3,tempfile
from contextlib import closing
from pathlib import Path
from core import DB,Fault,validate,submit,history,initialize

def load(path):
 if path.stat().st_size>32*1024*1024:raise Fault('exchange file exceeds 32 MiB')
 d=json.loads(path.read_text(encoding='utf-8-sig'))
 if not isinstance(d,dict) or set(d)!={'schema','events'} or d['schema']!='hub-status-exchange-v1' or not isinstance(d['events'],list) or len(d['events'])>1000:raise Fault('invalid exchange envelope; max 1000 status events')
 for e in d['events']:
  validate(e)
  if e['kind']!='status':raise Fault('exchange permits status only; owner definitions are separate')
 return d

def import_status(path,db=DB,apply=False):
 d=load(path)
 # Preflight against a transactionally consistent copy, never a live raw-file copy.
 with tempfile.TemporaryDirectory() as tmp:
  clone=Path(tmp)/'preview.sqlite3'
  with closing(sqlite3.connect(Path(db).resolve().as_uri()+'?mode=ro',uri=True)) as source,closing(sqlite3.connect(clone)) as target:source.backup(target)
  initialize(clone)
  results=[submit(e,clone) for e in d['events']]
 if not apply:return {'preview':True,'results':results,'note':'No writes to target. Revisions must still match when applying.'}
 # CAS protects each event; if concurrent writes cause a conflict, stop. Completed
 # events remain append-only; retry this exact file for idempotent continuation.
 applied=[]
 for e in d['events']:
  try:applied.append(submit(e,db))
  except Fault as ex:raise Fault('import stopped after '+str(len(applied))+' events: '+str(ex),ex.code)
 return {'preview':False,'results':applied}

def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
 x=s.add_parser('export');x.add_argument('project_id');x.add_argument('file',type=Path)
 x=s.add_parser('import');x.add_argument('file',type=Path);x.add_argument('--apply',action='store_true')
 a=p.parse_args()
 try:
  if a.command=='export':
   events=[r['payload'] for r in reversed(history(a.project_id)) if r['payload']['kind']=='status']
   if len(events)>1000:raise Fault('more than 1000 status events; split/review locally')
   with a.file.open('x',encoding='utf-8') as f:json.dump({'schema':'hub-status-exchange-v1','events':events},f,ensure_ascii=False,indent=2)
   print('Local export written; review/redact before sharing. No automatic upload.')
  else:print(json.dumps(import_status(a.file,apply=a.apply),ensure_ascii=False))
 except (Fault,OSError,ValueError) as ex:p.exit(1,str(ex)+'\n')
if __name__=='__main__':main()
