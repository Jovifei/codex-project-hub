import argparse,json,sqlite3
from pathlib import Path
from core import initialize,register,submit,ROOT,DB,overview,Fault
p=argparse.ArgumentParser(); s=p.add_subparsers(dest='command',required=True)
s.add_parser('list'); r=s.add_parser('catalog'); r.add_argument('file'); r=s.add_parser('catalog-export'); r.add_argument('name'); s.add_parser('init'); r=s.add_parser('apply'); r.add_argument('file'); r=s.add_parser('backup'); r.add_argument('name'); r=s.add_parser('export'); r.add_argument('name')
r=s.add_parser('catalog-history');r.add_argument('project_id');r.add_argument('--limit',type=int,default=50);r.add_argument('--before',type=int)
a=p.parse_args(); initialize()
try:
 if a.command=='init': register(json.loads((ROOT/'seed.json').read_text(encoding='utf-8'))); print('Example project records registered; no agent sessions changed')
 elif a.command=='list': print(json.dumps(overview(include_archived=True),ensure_ascii=False,indent=2))
 elif a.command=='catalog-history':
  from catalog import history
  print(json.dumps(history(a.project_id,limit=a.limit,before=a.before),ensure_ascii=False,indent=2))
 elif a.command=='catalog':
  from catalog import apply
  print(json.dumps(apply(json.loads(Path(a.file).read_text(encoding='utf-8-sig')))))
 elif a.command=='catalog-export':
  from catalog import export_catalog
  if Path(a.name).name!=a.name or not a.name.endswith('.json'):raise Fault('catalog basename must end .json')
  dest=ROOT/'exports'/a.name;dest.parent.mkdir(exist_ok=True)
  with dest.open('x',encoding='utf-8') as f:json.dump(export_catalog(),f,ensure_ascii=False,indent=2)
  print(dest)
 elif a.command=='apply': print(json.dumps(submit(json.loads(Path(a.file).read_text(encoding='utf-8-sig')),owner=True)))
 elif a.command=='backup':
  if Path(a.name).name!=a.name or not a.name.endswith('.sqlite3'): raise Fault('backup basename must end .sqlite3')
  dest=ROOT/'backups'/a.name; dest.parent.mkdir(exist_ok=True)
  if dest.exists(): raise Fault('backup already exists')
  with sqlite3.connect(DB) as src,sqlite3.connect(dest) as target: src.backup(target)
  print(dest)
 else:
  if Path(a.name).name!=a.name or not a.name.endswith('.html'): raise Fault('export basename must end .html')
  dest=ROOT/'exports'/a.name; dest.parent.mkdir(exist_ok=True)
  if dest.exists(): raise Fault('export already exists')
  data=overview(); template=(ROOT/'web/index.html').read_text(encoding='utf-8'); css=(ROOT/'web/style.css').read_text(encoding='utf-8'); js=(ROOT/'web/app.js').read_text(encoding='utf-8')
  import base64
  for proj in data['projects']: proj['art']='data:image/svg+xml;base64,'+base64.b64encode((ROOT/'web'/proj['art'].lstrip('/')).read_bytes()).decode()
  template=template.replace('<link rel="stylesheet" href="/style.css">','<style>'+css+'</style>').replace('<script src="/app.js" defer></script>','<script>window.SNAPSHOT='+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+';</script><script>'+js+'</script>')
  dest.write_text(template,encoding='utf-8'); print(dest)
except (Fault,OSError,ValueError) as ex: p.exit(1,str(ex)+'\n')
