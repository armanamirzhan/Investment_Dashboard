"""Shared UI snippets for in-browser workflow dispatch (PAT-based).

Both generate_dashboard.py and generate_reports.py embed REFRESH_JS + REFRESH_CSS.
The repo identity (OWNER/NAME) is read by the JS from a <meta> tag emitted by
each generator so the same code works in dev and on Pages.
"""

REPO_OWNER = "armanamirzhan"
REPO_NAME = "Investment_Dashboard"

REFRESH_CSS = r"""
.refresh-btn{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;font-size:11px;font-weight:500;background:var(--bg-hover);color:var(--text-secondary);border:1px solid var(--border);border-radius:6px;cursor:pointer;transition:all .15s;vertical-align:middle}
.refresh-btn:hover:not(:disabled){background:var(--accent-blue);color:#fff;border-color:var(--accent-blue)}
.refresh-btn:disabled{opacity:.7;cursor:wait}
.refresh-btn.status-success{background:rgba(58,184,103,0.15);color:#3AB867;border-color:#3AB867}
.refresh-btn.status-failed{background:rgba(232,84,84,0.15);color:#E85454;border-color:#E85454}
.refresh-btn.status-running{background:rgba(75,134,255,0.15);color:#4B86FF;border-color:#4B86FF}
.refresh-spinner{display:inline-block;width:10px;height:10px;border:2px solid currentColor;border-right-color:transparent;border-radius:50%;animation:rspin .8s linear infinite}
@keyframes rspin{to{transform:rotate(360deg)}}
.refresh-status{font-size:11px;color:var(--text-secondary);margin-left:8px}
.refresh-status .ok{color:#3AB867}
.refresh-status .err{color:#E85454}
.refresh-modal{position:fixed;inset:0;background:rgba(0,0,0,0.75);display:none;align-items:center;justify-content:center;z-index:9999}
.refresh-modal.open{display:flex}
.refresh-modal-box{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:24px;max-width:520px;width:90%;color:var(--text-primary)}
.refresh-modal-box h3{margin:0 0 12px}
.refresh-modal-box p{font-size:13px;color:var(--text-secondary);margin:8px 0}
.refresh-modal-box input{width:100%;padding:8px 10px;background:var(--bg-primary);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-family:monospace;font-size:12px;margin:8px 0 16px}
.refresh-modal-box .actions{display:flex;gap:8px;justify-content:flex-end}
.refresh-modal-box button{padding:8px 14px;font-size:13px;border:none;border-radius:6px;cursor:pointer}
.refresh-modal-box .primary{background:var(--accent-blue);color:#fff}
.refresh-modal-box .secondary{background:var(--bg-hover);color:var(--text-primary);border:1px solid var(--border)}
.refresh-modal-box a{color:var(--accent-blue)}
"""


def refresh_js() -> str:
    """JS that handles PAT capture, workflow dispatch, and run polling.

    Each refresh button declares its target via data attributes:
      data-workflow   workflow filename (e.g. refresh-section.yml)
      data-inputs     JSON string of inputs to send
      data-status-id  optional id of a status label element to update
    """
    return r"""
(function(){
  const OWNER=document.querySelector('meta[name="gh-owner"]')?.content;
  const REPO=document.querySelector('meta[name="gh-repo"]')?.content;
  const API="https://api.github.com";
  const PAT_KEY="gh_pat_v1";

  function getPAT(){return localStorage.getItem(PAT_KEY)||"";}
  function setPAT(v){if(v)localStorage.setItem(PAT_KEY,v);else localStorage.removeItem(PAT_KEY);}

  function ensureModal(){
    if(document.getElementById('refresh-modal'))return;
    const m=document.createElement('div');
    m.id='refresh-modal';m.className='refresh-modal';
    m.innerHTML=`<div class="refresh-modal-box">
      <h3>GitHub Personal Access Token</h3>
      <p>To trigger refresh workflows from this page, paste a fine-grained PAT with <strong>Actions: read & write</strong> permission on <code>${OWNER}/${REPO}</code>.</p>
      <p>Create one at <a href="https://github.com/settings/personal-access-tokens/new" target="_blank">github.com/settings/personal-access-tokens/new</a> &mdash; scope to this repo only.</p>
      <input id="refresh-pat-input" type="password" placeholder="github_pat_..." autocomplete="off">
      <div class="actions">
        <button class="secondary" id="refresh-pat-clear">Clear stored token</button>
        <button class="secondary" id="refresh-pat-cancel">Cancel</button>
        <button class="primary" id="refresh-pat-save">Save & continue</button>
      </div></div>`;
    document.body.appendChild(m);
    document.getElementById('refresh-pat-cancel').onclick=()=>closeModal(null);
    document.getElementById('refresh-pat-clear').onclick=()=>{setPAT("");closeModal(null);};
    document.getElementById('refresh-pat-save').onclick=()=>{
      const v=document.getElementById('refresh-pat-input').value.trim();
      if(v){setPAT(v);closeModal(v);}else closeModal(null);
    };
  }
  let modalResolve=null;
  function openModal(){
    ensureModal();
    const cur=getPAT();
    document.getElementById('refresh-pat-input').value=cur;
    document.getElementById('refresh-modal').classList.add('open');
    return new Promise(r=>{modalResolve=r;});
  }
  function closeModal(v){
    document.getElementById('refresh-modal').classList.remove('open');
    if(modalResolve){modalResolve(v);modalResolve=null;}
  }

  async function requirePAT(){
    let pat=getPAT();
    if(pat)return pat;
    pat=await openModal();
    return pat;
  }

  async function ghFetch(path,opts={}){
    const pat=getPAT();
    const headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28',...(opts.headers||{})};
    if(pat)headers['Authorization']='Bearer '+pat;
    const r=await fetch(API+path,{...opts,headers});
    return r;
  }

  async function dispatch(workflow,inputs){
    const r=await ghFetch(`/repos/${OWNER}/${REPO}/actions/workflows/${workflow}/dispatches`,{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({ref:'main',inputs:inputs||{}})
    });
    if(!r.ok){const t=await r.text();throw new Error(`Dispatch failed: ${r.status} ${t}`);}
    return true;
  }

  async function findLatestRun(workflow){
    // Look for the most recent run of this workflow within the last 60s
    const r=await ghFetch(`/repos/${OWNER}/${REPO}/actions/workflows/${workflow}/runs?per_page=5&event=workflow_dispatch`);
    if(!r.ok)return null;
    const j=await r.json();
    if(!j.workflow_runs||!j.workflow_runs.length)return null;
    // Pick the run we likely just triggered: created within the last 90s
    const now=Date.now();
    for(const run of j.workflow_runs){
      if(now-new Date(run.created_at).getTime()<90000)return run;
    }
    return j.workflow_runs[0];
  }

  async function pollRun(runId,onUpdate){
    while(true){
      const r=await ghFetch(`/repos/${OWNER}/${REPO}/actions/runs/${runId}`);
      if(!r.ok)throw new Error('Poll failed');
      const j=await r.json();
      onUpdate&&onUpdate(j);
      if(j.status==='completed')return j;
      await new Promise(res=>setTimeout(res,4000));
    }
  }

  function fmtTime(d){
    const dt=(typeof d==='string')?new Date(d):d;
    return dt.toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
  }

  function setBtnState(btn,state,text){
    btn.classList.remove('status-running','status-success','status-failed');
    if(state)btn.classList.add('status-'+state);
    const label=btn.querySelector('.refresh-label');
    if(label)label.textContent=text||label.dataset.idle||'Refresh';
    btn.disabled=(state==='running');
  }

  async function onClick(btn){
    const wf=btn.dataset.workflow;
    const inputs=btn.dataset.inputs?JSON.parse(btn.dataset.inputs):{};
    const statusEl=btn.dataset.statusId?document.getElementById(btn.dataset.statusId):null;
    const idleText=btn.querySelector('.refresh-label')?.textContent||'Refresh';
    btn.querySelector('.refresh-label')&&(btn.querySelector('.refresh-label').dataset.idle=idleText);

    const pat=await requirePAT();
    if(!pat){if(statusEl)statusEl.innerHTML='<span class="err">No token, cancelled.</span>';return;}

    try{
      setBtnState(btn,'running','Dispatching…');
      if(statusEl)statusEl.innerHTML='Triggering workflow…';
      await dispatch(wf,inputs);
      // Wait for run to appear
      await new Promise(r=>setTimeout(r,2500));
      const run=await findLatestRun(wf);
      if(!run){throw new Error('Run not found after dispatch');}
      setBtnState(btn,'running','Running…');
      if(statusEl)statusEl.innerHTML=`Run <a href="${run.html_url}" target="_blank">#${run.run_number}</a> queued…`;

      const final=await pollRun(run.id,(j)=>{
        if(statusEl){
          const status=j.status==='in_progress'?'Running':j.status;
          statusEl.innerHTML=`Run <a href="${j.html_url}" target="_blank">#${j.run_number}</a>: ${status}`;
        }
      });

      const ok=(final.conclusion==='success');
      setBtnState(btn,ok?'success':'failed',ok?'✓ Done':'✗ Failed');
      if(statusEl){
        statusEl.innerHTML=ok
          ? `<span class="ok">Updated ${fmtTime(final.updated_at)}</span> &middot; <a href="${final.html_url}" target="_blank">log</a>`
          : `<span class="err">Failed — see <a href="${final.html_url}" target="_blank">log</a></span>`;
      }
      // After success, reload after a short delay so the user sees fresh content
      if(ok)setTimeout(()=>location.reload(),3000);
    }catch(e){
      setBtnState(btn,'failed','✗ Error');
      if(statusEl)statusEl.innerHTML=`<span class="err">${e.message}</span>`;
      console.error(e);
    }
  }

  function wire(){
    document.querySelectorAll('.refresh-btn').forEach(btn=>{
      if(btn.dataset.wired)return;
      btn.dataset.wired='1';
      btn.addEventListener('click',()=>onClick(btn));
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire);
  else wire();
  window.__refreshUIWire=wire;
})();
"""


def refresh_meta_tags() -> str:
    """Meta tags so the JS knows which repo to talk to."""
    return f'<meta name="gh-owner" content="{REPO_OWNER}"><meta name="gh-repo" content="{REPO_NAME}">'


def refresh_modal_skeleton() -> str:
    """Empty div the JS will populate; kept here so HTML structure is explicit."""
    return ""


def section_button(section: str, label: str, ticker: str, last_updated: str = "") -> str:
    """Render a per-section refresh button + status label."""
    status_id = f"refresh-status-{section}-{ticker}"
    btn_id = f"refresh-btn-{section}-{ticker}"
    inputs = '{"ticker":"' + ticker + '","section":"' + section + '"}'
    last_html = (
        f'<span class="ok">Last refreshed {last_updated}</span>'
        if last_updated
        else '<span style="opacity:0.6">Not yet refreshed via button</span>'
    )
    return (
        f'<button class="refresh-btn" id="{btn_id}" '
        f'data-workflow="refresh-section.yml" '
        f"data-inputs='{inputs}' "
        f'data-status-id="{status_id}" '
        f'title="Refresh {label} via Claude agent">'
        f'<span class="refresh-label">↻ Refresh {label}</span></button>'
        f'<span class="refresh-status" id="{status_id}">{last_html}</span>'
    )


def metrics_button(last_updated: str = "") -> str:
    """Render the dashboard-level Refresh All Metrics button + status label."""
    last_html = (
        f'<span class="ok">Last refreshed {last_updated}</span>'
        if last_updated
        else '<span style="opacity:0.6">Awaiting first refresh</span>'
    )
    return (
        '<button class="refresh-btn" id="refresh-btn-metrics" '
        'data-workflow="refresh.yml" '
        "data-inputs='{}' "
        'data-status-id="refresh-status-metrics" '
        'title="Refresh all market data (price, P/E, market cap, etc.) for every public ticker">'
        '<span class="refresh-label">↻ Refresh All Metrics</span></button>'
        f'<span class="refresh-status" id="refresh-status-metrics">{last_html}</span>'
    )
