'use strict';
let data=null,filter='all',query='',selected={},histories={},online=true,lastFetch=null,lastMinute=-1;
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const list=a=>a?.length?'<ul class="list">'+a.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>':'<p class="muted">暂无记录 / 未知</p>';
const label={unknown:'已上报 · 当前工作未确认',active:'Agent 上报：进行中',blocked:'Agent 上报：受阻',paused:'Agent 上报：暂停',claimed_complete:'Agent 声称完成 · 待验证'};
const fmt=t=>t?new Date(t).toLocaleString('zh-CN',{hour12:false}):'未上报';
function state(s){if(!s?.status)return '未知 / 待上报';if(!online)return '断线 · 状态未知';if(!Number.isFinite(Date.parse(s.status.reported_at))||Date.parse(s.status.reported_at)>Date.now()+300000)return '上报时间异常 · 当前未知';if(Date.now()-Date.parse(s.status.reported_at)>86400000)return '信息过期 · 当前状态未知';return label[s.status.reported_status]||'未知'}
function streams(p){return p.streams.filter(s=>!s.is_test)}
function stream(p){const key=selected[p.project_id];if(key)return p.streams.find(s=>streamKey(s)===key);const real=streams(p);return real.length===1?real[0]:null}
function streamKey(s){return JSON.stringify([s.worktree_id,s.branch,s.is_test])}
function def(p,s){return s?.definition||p}
function counts(p,s){const d=def(p,s);return {verified:d.acceptance.filter(a=>s?.verification[a.id]?.outcome==='verified').length,total:d.acceptance.length}}
function segments(p,s){const d=def(p,s);return '<div class="segments" role="img" aria-label="阶段路线：'+esc(d.route.map(r=>r.name+(s?.status?.stage_id===r.id?'，当前上报阶段':'，未核实')).join('；'))+'">'+d.route.map(r=>'<i class="segment '+(s?.status?.stage_id===r.id?'active':'')+'" title="'+esc(r.name)+'"></i>').join('')+'</div>'}
function art(p){return '<img src="'+esc(p.art)+'" alt="'+esc(p.name)+' 产品概念插图">'}
function overview(){
 const real=data.projects.flatMap(streams),verified=real.reduce((n,s)=>n+Object.values(s.verification).filter(v=>v.outcome==='verified').length,0);
 $('crumb').textContent='总览';document.title='Local Hub · 项目总览';
 $('view').innerHTML='<span class="eyebrow">DELIVERY MAP / LOCAL WORKSPACE</span><h1>项目总览，一张交付地图</h1><p class="subtitle">看清目标、当前阶段与下一步；每次进展都有可追溯的记录。</p><div class="notice">目标与路线来自注册基线，确认来源与版本见详情。示例数据不代表真实工程。实时进展仅取自明确上报；测试记录单独展示。</div><div class="stats"><div class="stat"><small>注册项目</small><strong>'+data.projects.length+'</strong><span>独立详情与目标基线</span></div><div class="stat"><small>有真实上报的项目</small><strong>'+data.projects.filter(p=>streams(p).length).length+'</strong><span>不代表已自动连接会话</span></div><div class="stat"><small>人工记录的验证通过</small><strong>'+verified+'</strong><span>按工作树分别计数</span></div><div class="stat"><small>测试工作流</small><strong>'+data.projects.flatMap(p=>p.streams.filter(s=>s.is_test)).length+'</strong><span>不计入真实进展</span></div></div><div class="toolbar"><div class="filters" id="filters"></div><label><span class="muted">搜索 </span><input id="search" type="search" placeholder="项目、目标或分类" value="'+esc(query)+'" aria-label="搜索项目"></label></div><div class="grid" id="cards"></div><div class="notice">各项目、工作树与分支独立记录。验收可因回归重新打开，阶段条不代表整体百分比。</div>';
 const groups=['all',...new Set(data.projects.map(p=>p.category))];$('filters').innerHTML=groups.map(x=>'<button class="'+(x===filter?'on':'')+'" data-filter="'+esc(x)+'">'+esc(x==='all'?'全部项目':x)+'</button>').join('');$('filters').onclick=e=>{if(e.target.dataset.filter){filter=e.target.dataset.filter;overview()}};$('search').oninput=e=>{query=e.target.value;cards()};cards();
}
function cards(){const ps=data.projects.filter(p=>(filter==='all'||p.category===filter)&&[p.name,p.goal,p.category,p.project_id].join(' ').toLowerCase().includes(query.trim().toLowerCase()));$('cards').innerHTML=ps.map(p=>{const ss=streams(p),s=ss.length===1?ss[0]:null,c=counts(p,s);return '<a class="card" href="#project/'+p.project_id+'"><div class="art">'+art(p)+'<small>PROJECT '+String(p.number).padStart(2,'0')+'</small><span class="badge '+esc(s?.status?.reported_status||'')+'">'+esc(ss.length>1?'多个工作树 · 请选择':state(s))+'</span></div><div class="card-body"><h3>'+esc(p.name)+'</h3><p>'+esc(def(p,s).goal)+'</p><div class="counts"><span>已验证 / 总验收</span><b>'+c.verified+' / '+c.total+'</b></div>'+segments(p,s)+'<div class="card-line"><b>卡点</b>'+esc(s?.status?.blockers[0]||'尚未上报；当前未知')+'</div><div class="card-foot"><span>'+esc(p.category)+'</span><b>查看详情 →</b></div><small class="muted">最后上报：'+fmt(s?.status?.reported_at)+'</small></div></a>'}).join('')||'<div class="empty">没有匹配项目。请调整分类或搜索。</div>'}
function box(title,content,wide=false){return '<section class="box '+(wide?'wide':'')+'"><h2>'+title+'</h2>'+content+'</section>'}
function detail(p){
 const s=stream(p),d=def(p,s),c=counts(p,s),st=s?.status;
 $('crumb').textContent=p.name;document.title=p.name+' · Local Hub 项目管理台';
 $('view').innerHTML='<a class="back" href="#overview">← 返回项目总览</a><div class="hero"><div class="hero-copy"><span class="eyebrow">PROJECT '+String(p.number).padStart(2,'0')+' / '+esc(p.category)+'</span><h1>'+esc(p.name)+'</h1><p>'+esc(d.goal)+'</p><p class="path">'+esc(p.root)+'</p><div class="tags"><span class="badge">'+esc(state(s))+'</span>'+(s?.is_test?'<span class="badge test">明确标记的测试上报 · 非真实进展</span>':'')+'<span class="badge">revision '+(s?.revision||0)+'</span></div></div><div class="art">'+art(p)+'</div></div><div class="stream-picker"><label for="stream">工作树 / 分支</label><select id="stream"><option value="">'+(streams(p).length>1?'请选择工作树，避免混合状态':'目标基线 / 未选择上报')+'</option>'+p.streams.map(x=>'<option value="'+esc(streamKey(x))+'" '+(s===x?'selected':'')+'>'+esc((x.is_test?'[测试] ':'')+x.worktree_id+' / '+x.branch)+'</option>').join('')+'</select></div><div class="notice">基线来源：注册目录。目标与路线是历史资料；不代表已批准当前执行范围。普通上报不能修改目标。'+(st?' 最后上报 '+fmt(st.reported_at)+'；服务器接收 '+fmt(st.received_at)+'。':' 尚无所选工作树实时报告。')+'</div><div class="panels">'+box('阶段进度与技术路线','<div class="counts"><span>已验证 / 总验收</span><b>'+c.verified+' / '+c.total+'</b></div>'+segments(p,s)+'<p class="muted">蓝色表示 Agent 上报的当前阶段；其余阶段未核实。验收数量与阶段独立，不计算整体完成率。</p><div class="road">'+d.route.map((r,i)=>'<details class="'+(st?.stage_id===r.id?'active':'')+'"><summary><span class="step">'+(i+1)+'</span>'+esc(r.name)+'</summary><small>'+esc(r.id)+' · '+(st?.stage_id===r.id?'上报当前阶段':'未核实')+'</small><p>'+esc(r.detail)+'</p></details>').join('')+'</div>',true)+box('当前工作',list(st?.current))+box('下一步',list(st?.next))+box('卡点与待决事项',list(st?.blockers))+box('版本、测试与工件引用','<p class="muted">Agent 声明，仅展示引用，不运行或自动验证。</p><h3>版本</h3><div class="refs">'+list(st?.versions)+'</div><h3>测试</h3><div class="refs">'+list(st?.tests)+'</div><h3>工件</h3><div class="refs">'+list(st?.artifacts)+'</div>')+box('最终目标的验收证据','<div class="criteria">'+d.acceptance.map(a=>{const v=s?.verification[a.id],is=v?.outcome==='verified',claimed=st?.acceptance_claims.includes(a.id);return '<div class="criterion '+(is?'verified':'')+'"><span class="badge">'+esc(is?'人工记录：验证通过':v?.outcome==='reopened'?'回归：重新打开':v?.outcome==='needs_review'?'新报告后：需重验':claimed?'Agent 声称完成':'尚未核实')+'</span><p>'+esc(a.id)+' · '+esc(a.text)+'</p>'+(v?'<small>审核人 '+esc(v.reviewer)+' · '+fmt(v.verified_at)+'</small><div class="refs">'+list(v.evidence_refs)+'</div><p>'+esc(v.note)+'</p>':'')+'</div>'}).join('')+'</div><p class="muted" style="margin-top:15px">人工验证也是记录；系统不会替审核人认定证据真实。新状态报告会使此前验收待重验。</p>',true)+box('追加历史与最后有效快照','<div id="history">加载历史…</div>',true)+'</div><div class="bottom"><a href="#overview">← 项目总览</a><a href="#project/'+data.projects[(data.projects.indexOf(p)+1)%data.projects.length].project_id+'">下一个项目 →</a></div>';
 $('stream').onchange=e=>{selected[p.project_id]=e.target.value;detail(p)};loadHistory(p);
}
async function loadHistory(p,cursor=null,append=false){
 if(window.SNAPSHOT){$('history').innerHTML='<p class="muted">独立快照不含完整历史；历史在本机SQLite。</p>';return}
 const chosen=stream(p),expected=chosen?streamKey(chosen):'';
 try{const q=new URLSearchParams({limit:'50'});if(cursor)q.set('before',cursor);if(chosen)q.set('stream',expected);
  const res=await fetch('/api/history/'+p.project_id+'?'+q);if(!res.ok)throw Error('history');const h=await res.json();
  if(!location.hash.includes(p.project_id)||(stream(p)?streamKey(stream(p)):'')!==expected)return;
  const rows=append?[...(histories[p.project_id]||[]),...h.events]:h.events;histories[p.project_id]=rows;renderHistory(p,rows);
  if(h.next_cursor){$('history').insertAdjacentHTML('beforeend','<button id="history-more">加载更早记录</button>');$('history-more').onclick=()=>loadHistory(p,h.next_cursor,true)}
 }catch{if($('history'))$('history').innerHTML='<p>历史加载失败，请刷新；最后有效快照保留。</p>'}
}
function renderHistory(p,h){if(!$('history')||!location.hash.includes(p.project_id))return;const s=stream(p),rows=h.filter(x=>!s||(x.payload.worktree_id===s.worktree_id&&x.payload.branch===s.branch&&x.payload.is_test===s.is_test));$('history').innerHTML=rows.length?'<div class="timeline">'+rows.map(x=>'<article class="event"><time>'+fmt(x.received_at)+'</time><p><b>'+esc(x.payload.kind)+' · revision '+x.result.revision+'</b> '+(x.payload.is_test?'<span class="badge test">测试</span>':'')+'</p><p>'+esc(x.payload.agent_id+' / '+x.payload.run_id+' · '+x.payload.worktree_id+' / '+x.payload.branch)+'</p><details><summary>事件 '+esc(x.payload.event_id)+' · 展开记录</summary><pre>'+esc(JSON.stringify(x.payload,null,2))+'</pre></details></article>').join('')+'</div>':'<p class="muted">暂无上报事件。注册项目不会自动连接 Agent。</p>'}
function navigate(){if(!data)return;const m=location.hash.match(/^#project\/([a-zA-Z0-9_.-]+)$/);const p=m&&data.projects.find(p=>p.project_id===m[1]);if(m&&!p){$('view').innerHTML='<div class="empty">项目不存在。<a href="#overview">返回总览</a></div>';return}p?detail(p):overview();document.querySelectorAll('.nav').forEach(a=>a.classList.toggle('active',a.hash===(p?'#project/'+p.project_id:'#overview')))}
function renderNav(){$('nav').innerHTML=data.projects.map(p=>'<a class="nav" href="#project/'+p.project_id+'"><span>'+String(p.number).padStart(2,'0')+'</span>'+esc(p.name)+'</a>').join('')}
async function refresh(){if(window.SNAPSHOT){data=window.SNAPSHOT;online=false;$('connection').textContent='离线快照 · '+fmt(data.server_time);$('refresh').hidden=true;renderNav();navigate();return}try{const r=await fetch('/api/projects',{cache:'no-store',signal:AbortSignal.timeout(4000)});if(!r.ok)throw Error('HTTP '+r.status);const next=await r.json();const minute=Math.floor(Date.now()/60000),changed=JSON.stringify(data?.projects)!==JSON.stringify(next.projects)||!online||minute!==lastMinute;lastMinute=minute;data=next;online=true;lastFetch=new Date();$('connection').textContent='已更新 '+lastFetch.toLocaleTimeString('zh-CN',{hour12:false});$('error').hidden=true;if(changed){renderNav();navigate()} }catch(ex){online=false;$('connection').textContent='服务断线 · 当前状态未知';$('error').hidden=false;$('error').textContent='无法连接本机服务。保留最后有效快照，请检查服务并点击刷新。断线不代表 Agent 停工。';if(data)navigate();else $('view').innerHTML='<div class="empty">暂无可用数据。启动服务后刷新。</div>'}}
if(!location.hash&&location.pathname.startsWith('/project/'))location.hash='#project/'+location.pathname.split('/')[2];
window.addEventListener('hashchange',()=>{navigate();window.scrollTo(0,0)});$('refresh').onclick=refresh;refresh();if(!window.SNAPSHOT)setInterval(refresh,5000);

/* BEGIN:hub-five-delivery-v1 */
const deliveryNames=['代码提交','精确 CI','本机验证','安装 / 部署','真实验收'];
const deliveryStates={recorded:'已记录 · 未验证',passed:'通过回执 · 非最终验收',failed:'失败 / 需修',pending:'待验证',partial:'部分通过',blocked:'受阻',unknown:'未知'};
function deliveryMeta(s){
 if(!s?.status||s.is_test||!Array.isArray(s.status.artifacts))return null;
 try{const raw=s.status.artifacts.find(x=>typeof x==='string'&&x.startsWith('hub_delivery_v1:'));if(!raw)return null;const d=JSON.parse(raw.slice(16));
  if(d.version!==1||d.project_id!==s.status.project_id||!Number.isFinite(Date.parse(d.check_time))||Date.parse(d.check_time)>Date.now()+300000||!Array.isArray(d.phases)||d.phases.length!==5)return null;
  if(d.phases.some(p=>!p||!Object.hasOwn(deliveryStates,p.state)||typeof p.note!=='string'||typeof p.evidence_at!=='string'))return null;
  if(!Array.isArray(d.evidence_links)||d.evidence_links.some(u=>typeof u!=='string'))return null;
  if(['owner','check_scope','source_role','last_actual_progress'].some(k=>typeof d[k]!=='string'))return null;
  return d;
 }catch{return null}
}
function deliveryStream(p){
 const chosen=selected[p.project_id],real=streams(p),s=chosen?p.streams.find(s=>streamKey(s)===chosen):(real.length===1?real[0]:null);
 return s&&deliveryMeta(s)?.project_id===p.project_id?s:null;
}
function deliveryBadge(s){return state(s)+' · 协调回执 / 待独立验收'}
function deliveryBar(m,full=false){return '<div class="delivery-stages '+(full?'delivery-full':'')+'" aria-label="五阶段交付回执">'+m.phases.map((phase,i)=>'<'+(full?'section':'div')+' class="delivery-stage '+esc(phase.state)+'"><b>'+deliveryNames[i]+'</b><span>'+deliveryStates[phase.state]+'</span>'+(full?'<p>'+esc(phase.note)+'</p><small>证据时刻：'+esc(phase.evidence_at)+'</small>':'')+'</'+(full?'section':'div')+'>').join('')+'</div>'}
function deliveryTiming(m){return '<div class="delivery-timing"><b>本轮核对：</b>'+esc(fmt(m.check_time))+'<br><b>最后实际工程进展：</b>'+esc(m.last_actual_progress_at?fmt(m.last_actual_progress_at):'精确时刻未提供')+'<br><span>'+esc(m.last_actual_progress)+'</span></div>'}
const deliveryOriginalStream=stream;
stream=function(p){if(selected[p.project_id])return deliveryOriginalStream(p);return deliveryStream(p)||deliveryOriginalStream(p)};
const deliveryOriginalCards=cards;
cards=function(){deliveryOriginalCards();document.querySelectorAll('#cards .card').forEach(card=>{const pid=card.getAttribute('href').split('/').pop(),p=data.projects.find(x=>x.project_id===pid),s=p&&deliveryStream(p),m=deliveryMeta(s);if(!m)return;card.classList.add('has-delivery');const badge=card.querySelector('.art .badge');badge.textContent=deliveryBadge(s);const body=card.querySelector('.card-body'),oldSegments=body.querySelector('.segments'),oldCounts=body.querySelector('.counts');if(oldCounts)oldCounts.remove();if(oldSegments)oldSegments.outerHTML=deliveryBar(m);const line=body.querySelector('.card-line');line.innerHTML='<b>卡点</b>'+esc(s.status.blockers[0]||'未核实');const oldTime=body.querySelector('small.muted');if(oldTime)oldTime.remove();body.insertAdjacentHTML('beforeend',deliveryTiming(m)+'<small class="delivery-owner">'+esc(m.owner)+'</small>')})};
const deliveryOriginalDetail=detail;
detail=function(p){deliveryOriginalDetail(p);const s=stream(p),m=deliveryMeta(s);if(!m)return;const panel=document.querySelector('.panels');const urls=m.evidence_links.filter(u=>/^https:\/\/github\.com\//.test(u));panel.insertAdjacentHTML('beforebegin','<section class="box delivery-detail"><h2>五阶段交付回执</h2><p class="muted">提交、CI、本机、部署与真实验收分别记录；回执通过不等于已独立验证，不换算整体百分比。</p>'+deliveryBar(m,true)+deliveryTiming(m)+'<p class="delivery-owner">负责方式：'+esc(m.owner)+'</p><p class="muted">'+esc(m.check_scope)+'。'+esc(m.source_role)+'。</p><p class="delivery-links">'+urls.map((u,i)=>'<a href="'+esc(u)+'" target="_blank" rel="noopener noreferrer">'+(i===0?'提交证据':'CI '+u.split('/').pop())+' ↗</a>').join(' · ')+'</p></section>');const title=panel.querySelector('.box h2');if(title)title.textContent='原有目标与技术路线（与交付阶段分开）'};
if(data)navigate();
/* END:hub-five-delivery-v1 */


/* BEGIN:hub-evidence-v1-pure */
const evidenceLabels={recorded:'代码记录 · 未代表交付',passed_record:'CI / 回执通过 · 本轮未独立验证',passed_verified:'CI 归档已独立核对 · 非真实验收',partial:'部分通过',failed:'失败',blocked:'阻塞',not_received:'尚未接收',unverified:'待验证',historical:'历史记录 · 不代表当前版本',unknown:'未知'};
function evidenceMeta(s){
 if(!s?.status||s.is_test)return null;
 try{const raw=s.status.artifacts?.find(a=>typeof a==='string'&&a.startsWith('hub_evidence_v1:'));if(!raw)return null;const m=JSON.parse(raw.slice(16));
  if(m.version!==1||m.project_id!==s.status.project_id||!Number.isFinite(Date.parse(m.checkedAt))||typeof m.source!=='string'||!Array.isArray(m.accessGaps))return null;
  const p=m.project;if(!p||typeof p.goal!=='string'||typeof p.current!=='string'||typeof p.next!=='string'||!Number.isFinite(Date.parse(p.lastEngineeringAt))||!Array.isArray(p.blockers)||!Array.isArray(p.stages)||!p.stages.length||p.stages.length>30)return null;
  if(p.stages.some(x=>!x||typeof x.id!=='string'||typeof x.title!=='string'||typeof x.detail!=='string'||!Object.hasOwn(evidenceLabels,x.status)||!Array.isArray(x.evidence)||x.evidence.some(u=>typeof u!=='string')))return null;
  if(new Set(p.stages.map(x=>x.id)).size!==p.stages.length)return null;
  return m;
 }catch{return null}
}
function evidenceLatest(p){if(selected[p.project_id]){const s=p.streams.find(s=>streamKey(s)===selected[p.project_id]);return evidenceMeta(s)?.project_id===p.project_id?s:null}return p.streams.filter(s=>s.worktree_id==='coordination:five-project-receipts'&&s.branch==='evidence-summary-only'&&evidenceMeta(s)?.project_id===p.project_id).sort((a,b)=>Date.parse(b.status.reported_at)-Date.parse(a.status.reported_at))[0]||null}
function evidenceAge(m,isOnline=online,now=Date.now()){return !isOnline?'离线 · 当前未知':(!Number.isFinite(Date.parse(m.checkedAt))||Date.parse(m.checkedAt)>now+300000)?'核对时间异常 · 当前未知':now-Date.parse(m.checkedAt)>86400000?'核对记录过期 · 当前未知':'最近核对快照 · 非实时执行'}
function evidenceLink(u){try{const v=new URL(u);if(v.protocol!=='https:'||v.hostname!=='github.com'||v.username||v.password)return '';const label=v.pathname.includes('/actions/')?'CI 运行记录':v.hash.startsWith('#issuecomment-')?'PR 交接回执':v.pathname.includes('/pull/')?'PR 代码 / 讨论':v.pathname.includes('/blob/')?'仓库文档记录':v.pathname.includes('/commit/')?'提交记录':'GitHub 证据记录';return '<a href="'+esc(v.href)+'" target="_blank" rel="noopener noreferrer">'+label+' ↗</a>'}catch{return ''}}
function evidenceStages(m){return '<div class="evidence-road">'+m.project.stages.map((s,i)=>'<details class="evidence-step '+esc(s.status)+'"><summary><span class="step">'+(i+1)+'</span><strong>'+esc(s.title)+'</strong><span class="badge">'+esc(evidenceLabels[s.status])+'</span></summary><p>'+esc(s.detail)+'</p><p class="delivery-links">'+s.evidence.map(evidenceLink).filter(Boolean).join(' · ')+'</p></details>').join('')+'</div>'}
/* END:hub-evidence-v1-pure */
/* A management report is identified by its source marker and required columns,
   never by a fixed project allowlist. Real engineering streams remain selectable. */
const evidenceStoredMeta=evidenceMeta;
function managementMeta(s){
 if(!s?.status||s.is_test||s.status.kind!=='status')return null;
 // Valid structured same-stream evidence is authoritative as a whole. Never combine
 // legacy summary values with its newer checkedAt; legacy rows are fallback only.
 const rich=evidenceStoredMeta(s);if(rich)return rich;
 const st=s.status,rows=st.current;
 if(st.artifacts?.some(a=>typeof a==='string'&&a.startsWith('hub_evidence_v1:'))&&!evidenceStoredMeta(s))return null;
 if(!Array.isArray(rows)||!st.artifacts?.some(a=>typeof a==='string'&&(a.startsWith('hub_evidence_v1:')||a.startsWith('管理证据来源：'))))return null;
 const read=prefix=>rows.find(x=>typeof x==='string'&&x.startsWith(prefix))?.slice(prefix.length).trim();
 const goal=read('最终可观察效果（管理摘要，未改Owner目标）：'),phase=read('当前阶段：'),action=read('最近确认动作（来源分层）：'),decision=read('当前责任分工；最后有效用户决定 '),accepted=read('已验收与仅回执：'),coverage=read('读取覆盖：');
 if([goal,phase,action,decision,accepted,coverage].some(x=>!x)||!Number.isFinite(Date.parse(st.reported_at)))return null;
 const next=st.next?.find(x=>x.startsWith('下一阶段：'))?.slice(5),acceptance=st.next?.find(x=>x.startsWith('验收条件：'))?.slice(5);
 if(!next||!acceptance)return null;
 return {version:1,project_id:st.project_id,checkedAt:rich?.checkedAt||st.reported_at,source:rich?.source||'管理证据来源：显式导入；未重新验证业务。',notice:rich?.notice||'显式导入的管理快照；正式目标与工程工作流独立。',accessGaps:rich?.accessGaps||['远端网页会话与附件未直接读取；长消息摘录有截断。','今天零消息是读取覆盖缺口，不等于停工；旧回执不能替代当前版本验收。'],project:{...(rich?.project||{}),goal,current:phase,next,blockers:st.blockers,repository:rich?.project.repository||'注册项目管理记录',lastEngineeringAt:rich?.project.lastEngineeringAt||null,action,decision,accepted,coverage,acceptance,stages:rich?.project.stages||[{id:'actions',title:'最近确认动作与证据边界',status:'unverified',detail:action+' '+accepted,evidence:[]},{id:'decision',title:'当前分工与最后用户决定',status:'recorded',detail:decision,evidence:[]},{id:'coverage',title:'读取覆盖与证据时效',status:'unknown',detail:coverage,evidence:[]}]}};
}
evidenceMeta=function(s){return managementMeta(s)||evidenceStoredMeta(s)};
const evidenceOriginalStream=stream;
stream=function(p){return selected[p.project_id]?evidenceOriginalStream(p):(evidenceLatest(p)||evidenceOriginalStream(p))};
const evidenceOriginalCards=cards;
const brief=(text,n=100)=>String(text||'未提供 / 未知').length>n?String(text).slice(0,n)+'…':String(text||'未提供 / 未知');
cards=function(){
 evidenceOriginalCards();document.querySelectorAll('#cards .card').forEach(card=>{
  const p=data.projects.find(p=>p.project_id===card.getAttribute('href').split('/').pop()),s=p&&evidenceLatest(p),m=evidenceMeta(s);if(!m)return;
  const body=card.querySelector('.card-body');card.classList.add('has-management');card.querySelector('.art .badge').textContent=state(s)+' · '+evidenceAge(m);
  body.querySelectorAll('.evidence-card-work').forEach(x=>x.remove());
  body.querySelector('h3').insertAdjacentHTML('afterend','<div class="evidence-card-work"><b>当前阶段</b><p>'+esc(brief(m.project.current))+'</p><b>当前分工</b><p>'+esc(brief(m.project.decision||'见详情阶段记录',105))+'</p></div>');
  const line=body.querySelector('.card-line');line.innerHTML='<b>关键卡点</b>'+esc(brief(m.project.blockers[0],85));line.insertAdjacentHTML('afterend','<div class="card-line management-next"><b>下一步</b>'+esc(brief(m.project.next,85))+'</div>');
  let time=body.querySelector('.delivery-timing');if(!time){body.insertAdjacentHTML('beforeend','<div class="delivery-timing"></div>');time=body.querySelector('.delivery-timing')}
  time.innerHTML='<b>证据核对：</b>'+esc(fmt(m.checkedAt))+'<br><small>工程推进时刻、来源与覆盖见详情</small>';
 });
};
const evidenceOriginalOverview=overview;
overview=function(){evidenceOriginalOverview();document.querySelector('#view .notice')?.insertAdjacentHTML('afterend','<div class="notice management-scope">看板只展示当前已登记且未归档项目；候选目录不代表完整项目总数。证据窗口与工程推进时间分别记录；未读到不等于停工。默认显示有效管理证据，工程工作树可在详情另选。</div>')};
const evidenceOriginalDetail=detail;
detail=function(p){
 evidenceOriginalDetail(p);const s=stream(p),m=evidenceMeta(s);if(!m||m.project_id!==p.project_id)return;
 const panel=document.querySelector('.panels'),v=m.project;
 panel.insertAdjacentHTML('beforebegin','<section class="box evidence-detail"><h2>管理证据 · '+esc(evidenceAge(m))+'</h2><p class="muted">'+esc(m.notice)+' 页面每5秒刷新共享数据，不自动读取全部会话；断线不代表Agent停工。</p><div class="evidence-summary"><div><h3>最终可观察效果</h3><p>'+esc(v.goal)+'</p><h3>当前阶段</h3><p>'+esc(v.current)+'</p></div><div><h3>最近确认动作</h3><p>'+esc(v.action||v.current)+'</p><h3>已验收与仅回执</h3><p>'+esc(v.accepted||'各条来源见阶段记录；未新增真实验收。')+'</p></div><div><h3>关键卡点</h3>'+list(v.blockers)+'</div></div><h3>当前分工 / 最后用户决定时间</h3><p class="management-decision">'+esc(v.decision||'此证据未提供当前责任分工；未知')+'</p><h3>下一阶段</h3><p>'+esc(v.next)+'</p><h3>验收条件</h3><p>'+esc(v.acceptance||'见阶段记录，尚待确认')+'</p><h3>读取覆盖与证据时效</h3><p>'+esc(v.coverage||'此记录未提供会话覆盖；未知')+' 未读到属于覆盖缺口，不等于停工。</p><p>证据核对：'+esc(fmt(m.checkedAt))+' · 最近工程记录：'+esc(v.lastEngineeringAt?fmt(v.lastEngineeringAt):'未提供，不能以导入时间代替')+'</p><p class="muted">来源：'+esc(m.source)+'</p>'+evidenceStages(m)+'<details><summary>证据访问缺口 / 范围</summary>'+list(m.accessGaps)+'</details></section>');
 const legacy=document.querySelector('.delivery-detail');if(legacy){legacy.querySelectorAll('.delivery-stage small').forEach(x=>x.textContent='单条证据时刻见明细；核对时刻：'+fmt(m.checkedAt));const t=legacy.querySelector('.delivery-timing');if(t)t.innerHTML='证据核对：'+esc(fmt(m.checkedAt))+'<br>最近工程记录：'+esc(v.lastEngineeringAt?fmt(v.lastEngineeringAt):'未提供');legacy.querySelectorAll('p.muted').forEach(x=>x.textContent='五阶段来自协调证据；回执通过不等于本机验证或真实验收。来源与版本见下方。')}
 document.querySelectorAll('.delivery-detail .delivery-links a').forEach(a=>{a.outerHTML=evidenceLink(a.href)});document.querySelectorAll('.panels .refs li').forEach(li=>{if(li.textContent.startsWith('hub_evidence_v1:')||li.textContent.startsWith('hub_delivery_v1:'))li.textContent='结构化协调证据：见管理证据视图；完整原文保留在追加历史。'});
};
if(data)navigate();

function goalProvenance(p,s){
 const g=(s?s.goal_provenance:p.goal_provenance)||{status:'unconfirmed'};
 return '<section class="box goal-provenance"><h2>目标定义来源与确认</h2><span class="badge">'+(g.status==='confirmed'?'人工确认记录（系统未自动判真）':'目标待负责人确认')+'</span><p>'+esc(g.source_ref||'尚未提供确认来源')+'</p><p>版本：'+esc(g.version||'未知')+' · 批准人：'+esc(g.approved_by||'未知')+' · '+esc(g.approved_at?fmt(g.approved_at):'未批准')+'</p>'+list(g.evidence_refs)+'</section>';
}
const provenanceDetail=detail;
detail=function(p){
 provenanceDetail(p);const s=stream(p),rich=evidenceStoredMeta(s);
 document.querySelector('.hero')?.insertAdjacentHTML('afterend',goalProvenance(p,s));
 // Existing ledgers can contain legacy prefix fields alongside a newer structured
 // object. Display one source consistently; raw payload stays in immutable history.
 if(rich?.project_id===p.project_id)document.querySelectorAll('.panels > .box').forEach(box=>{
  const title=box.querySelector('h2')?.textContent;
  if(title==='当前工作')box.innerHTML='<h2>当前工作（结构化证据）</h2>'+list([rich.project.current]);
  if(title==='下一步')box.innerHTML='<h2>下一步（结构化证据）</h2>'+list([rich.project.next]);
 });
};
const temporalCards=cards;
cards=function(){temporalCards();document.querySelectorAll('#cards .card').forEach(card=>{const p=data.projects.find(p=>p.project_id===card.getAttribute('href').split('/').pop()),s=p&&(evidenceLatest(p)||deliveryStream(p)||stream(p));if(!online||(s?.status&&(!Number.isFinite(Date.parse(s.status.reported_at))||Date.now()-Date.parse(s.status.reported_at)>86400000||Date.parse(s.status.reported_at)>Date.now()+300000)))card.querySelector('.art .badge').className='badge unknown'})};
