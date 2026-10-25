import json, argparse
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,unquote,parse_qs
from core import ROOT,DB,initialize,overview,history,history_page,submit,Fault

class Handler(BaseHTTPRequestHandler):
 def send(self,code,data,mime='application/json; charset=utf-8'):
  body=json.dumps(data,ensure_ascii=False).encode() if mime.startswith('application/json') else data
  self.send_response(code); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','no-referrer'); self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'"); self.end_headers(); self.wfile.write(body)
 def safe_host(self):
  return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
 def do_GET(self):
  if not self.safe_host(): return self.send(403,{'error':'invalid host'})
  path=unquote(urlparse(self.path).path)
  if path=='/api/projects': return self.send(200,overview())
  if path.startswith('/api/history/'):
   pid=path.split('/')[-1]
   if pid not in {p['project_id'] for p in overview(include_archived=True)['projects']}: return self.send(404,{'error':'unknown project'})
   try:
    q=parse_qs(urlparse(self.path).query,keep_blank_values=True)
    if any(k not in {'limit','before','stream'} or len(v)!=1 for k,v in q.items()):raise Fault('invalid history query')
    page=history_page(pid,limit=int(q.get('limit',['50'])[0]),before=int(q['before'][0]) if 'before' in q else None,stream=json.loads(q['stream'][0]) if 'stream' in q else None)
    return self.send(200,page if q else page['events'])
   except (Fault,ValueError,TypeError) as ex:return self.send(400,{'error':str(ex)})
  if path=='/api/health': return self.send(200,{'ok':True})
  if path in ('/','/index.html') or path.startswith('/project/'): return self.send(200,(ROOT/'web/index.html').read_bytes(),'text/html; charset=utf-8')
  if path in ('/app.js','/style.css'): return self.send(200,(ROOT/'web'/path[1:]).read_bytes(),'text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8')
  if path.startswith('/art/'):
   name=path.split('/')[-1]
   if path!=f'/art/{name}' or name not in {str(i)+'.svg' for i in range(1,10)}: return self.send(404,{'error':'not found'})
   return self.send(200,(ROOT/'web/art'/name).read_bytes(),'image/svg+xml')
  return self.send(404,{'error':'not found'})
 def do_POST(self):
  origin=self.headers.get('Origin')
  if not self.safe_host() or (origin and origin not in {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}): return self.send(403,{'error':'cross-origin / host rejected'})
  if self.path!='/api/events': return self.send(404,{'error':'not found'})
  if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.send(415,{'error':'JSON required'})
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=65536: raise Fault('body too large or empty',413)
   e=json.loads(self.rfile.read(size)); self.send(200,submit(e))
  except Fault as ex: self.send(ex.code,{'error':str(ex)})
  except (ValueError,UnicodeError): self.send(400,{'error':'malformed JSON'})
 def log_message(self,*args): pass
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=8765); a=p.parse_args(); initialize(); s=ThreadingHTTPServer(('127.0.0.1',a.port),Handler); print(f'Project Hub http://127.0.0.1:{a.port}',flush=True)
 try: s.serve_forever()
 except KeyboardInterrupt: pass
 finally: s.server_close()
