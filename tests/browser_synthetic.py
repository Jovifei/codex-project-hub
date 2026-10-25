"""Own temporary synthetic DB/server only. Requires Python Playwright + Edge/Chromium."""
import argparse,json,os,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--evidence-dir',type=Path,default=ROOT/'reports'/'synthetic-validation');a=ap.parse_args();a.evidence_dir.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='hub-synthetic-') as temp:
  os.environ['HUB_DATA_DIR']=temp;sys.path.insert(0,str(ROOT));import core
  core.initialize();projects=json.loads((ROOT/'seed.json').read_text(encoding='utf-8'));core.register(projects)
  def report(pid,eid,revision=0,branch='main',artifacts=None,reported='2020-01-01T00:00:00Z'):
   return dict(schema_version=1,kind='status',event_id=eid,project_id=pid,agent_id='synthetic-agent',run_id='synthetic-run',worktree_id='synthetic-worktree',branch=branch,expected_revision=revision,reported_at=reported,is_test=False,reported_status='active',stage_id='s1',current=['Synthetic work only'],next=['Synthetic next step'],blockers=[],versions=[],tests=[],artifacts=artifacts or [],acceptance_claims=[])
  def metadata(pid):return dict(version=1,project_id=pid,phases=[dict(state='pending',note='Synthetic evidence',evidence_at=core.now()) for _ in range(5)],evidence_links=[],check_time=core.now(),last_actual_progress='Synthetic progress',owner='Synthetic owner',check_scope='Synthetic scope',source_role='Synthetic source')
  for i in range(65):core.submit(report('example-1',f'synthetic-{i}',i,artifacts=['hub_delivery_v1:'+json.dumps(metadata('example-1'))]))
  bad=metadata('example-2');bad['evidence_links']={};core.submit(report('example-2','malformed',artifacts=['hub_delivery_v1:'+json.dumps(bad)]))
  for branch in ('main','other'):core.submit(report('example-3','multiple-'+branch,branch=branch,reported=core.now(),artifacts=['hub_delivery_v1:'+json.dumps(metadata('example-3'))]))
  rich={'version':1,'project_id':'example-4','checkedAt':core.now(),'source':'Synthetic new structured source','notice':'Synthetic precedence regression','accessGaps':[],'project':{'goal':'NEW STRUCTURED GOAL','current':'NEW STRUCTURED PHASE','next':'NEW STRUCTURED NEXT','blockers':['NEW STRUCTURED BLOCKER'],'lastEngineeringAt':'2026-10-10T00:00:00Z','stages':[{'id':'acceptance','title':'Recorded only','status':'recorded','detail':'No acceptance verification','evidence':[]}]}}
  legacy=metadata('example-4');legacy['phases']=[{**x,'state':'recorded'} for x in legacy['phases']]
  e=report('example-4','legacy-versus-rich',reported=core.now(),artifacts=['hub_evidence_v1:'+json.dumps(rich),'hub_delivery_v1:'+json.dumps(legacy)]);e.update(worktree_id='coordination:five-project-receipts',branch='evidence-summary-only',current=['最终可观察效果（管理摘要，未改Owner目标）：OLD LEGACY GOAL','当前阶段：OLD LEGACY PHASE','最近确认动作（来源分层）：OLD LEGACY ACTION','当前责任分工；最后有效用户决定 OLD LEGACY DECISION','已验收与仅回执：OLD LEGACY ACCEPTED','读取覆盖：OLD LEGACY COVERAGE'],next=['下一阶段：OLD LEGACY NEXT','验收条件：OLD LEGACY ACCEPTANCE']);core.submit(e)
  with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  log=open(Path(temp)/'server.log','w');proc=subprocess.Popen([sys.executable,'-B','server.py','--port',str(port)],cwd=ROOT,env=os.environ.copy(),stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
  base=f'http://127.0.0.1:{port}';checks=[];errors=[]
  try:
   for _ in range(80):
    try:
     with urllib.request.urlopen(base+'/api/health',timeout=.5) as r:assert r.status==200
     break
    except OSError:time.sleep(.1)
   else:raise RuntimeError('synthetic server failed to start')
   with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,**({'channel':'msedge'} if os.name=='nt' else {}));context=browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base,wait_until='networkidle');assert page.locator('#cards .card').count()==9
    assert '过期' in page.locator('#cards .card').first.inner_text();page.screenshot(path=str(a.evidence_dir/'overview.png'),full_page=True);checks.append('Nine synthetic cards; stale badge retained')
    page.locator('#search').fill('NO-MATCH');assert page.locator('#cards .empty').count()==1;page.locator('#search').fill('example-1');assert page.locator('#cards .card').count()==1;page.locator('#search').fill('')
    page.locator('#filters button[data-filter]:not([data-filter="all"])').first.click();assert 0<page.locator('#cards .card').count()<9;page.locator('#filters button[data-filter="all"]').click()
    page.goto(base+'/#project/example-1',wait_until='networkidle');page.wait_for_selector('#history-more');assert page.locator('#history .event').count()==50;page.locator('#history-more').click();page.wait_for_function("() => document.querySelectorAll('#history .event').length===65");assert '目标待负责人确认' in page.locator('.goal-provenance').inner_text();checks.append('50+15 history paging; unconfirmed provenance visible')
    page.goto(base+'/#project/example-2',wait_until='networkidle');assert page.locator('.delivery-detail').count()==0;checks.append('Malformed delivery links ignored without crash')
    page.goto(base+'/#project/example-3',wait_until='networkidle');assert page.locator('.delivery-detail').count()==0;page.locator('#stream').select_option(json.dumps(['synthetic-worktree','main',False],separators=(',',':')));assert page.locator('.delivery-detail').count()==1;checks.append('Multiple streams require selection; selected stream respected')
    page.goto(base+'/#project/example-4',wait_until='networkidle');text=page.locator('.evidence-detail').inner_text();assert 'NEW STRUCTURED PHASE' in text and 'NEW STRUCTURED NEXT' in text and 'OLD LEGACY PHASE' not in text and 'OLD LEGACY NEXT' not in text;assert '已记录' in page.locator('.delivery-detail .delivery-stage').nth(4).inner_text();assert '通过' not in page.locator('.delivery-detail .delivery-stage').nth(4).inner_text();panels=page.locator('.panels').inner_text();assert 'OLD LEGACY PHASE' not in panels and 'OLD LEGACY NEXT' not in panels;checks.append('Structured source wins in management and current/next panels without legacy fields/new clock mixing; recorded acceptance never displays passed');page.screenshot(path=str(a.evidence_dir/'precedence.png'),full_page=True)
    for project in projects:
     page.goto(base+'/#project/'+project['project_id'],wait_until='networkidle');page.wait_for_selector('.hero');page.locator('a.back').click();page.wait_for_selector('#cards .card');assert page.locator('#cards .card').count()==9
    checks.append('All nine details and return navigation')
    context.set_offline(True);page.locator('#refresh').click();page.wait_for_selector('#error:not([hidden])');assert '未知' in page.locator('#connection').inner_text();assert '断线' in page.locator('#cards .card').first.inner_text();context.set_offline(False);page.locator('#refresh').click();page.wait_for_selector('#error[hidden]',state='attached');checks.append('Offline last snapshot and recovery; stale/offline not masked')
    page.set_viewport_size({'width':390,'height':844})
    for route in ['#overview']+['#project/'+p['project_id'] for p in projects]:
     page.goto(base+'/'+route,wait_until='networkidle');assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth'),route
    checks.append('390px overview and nine details without overflow')
    page.goto(base+'/#project/does-not-exist',wait_until='networkidle');assert '项目不存在' in page.locator('#view').inner_text();assert errors==[],errors
    page.goto(base,wait_until='networkidle');page.screenshot(path=str(a.evidence_dir/'mobile.png'),full_page=True)
    browser.close()
   out={'synthetic_only':True,'checks':checks,'page_errors':errors,'result':'passed'};(a.evidence_dir/'browser.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
  finally:proc.terminate();proc.wait(timeout=10);log.close()
if __name__=='__main__':main()
