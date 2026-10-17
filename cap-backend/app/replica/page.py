PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Court Access Portal (local replica)</title>
<style>
:root { --ink:#0f172a; --muted:#64748b; --line:#e2e8f0; --brand:#1e4e8c; --brand-dark:#163a6b; --soft:#eef3f9; --ok:#047857; --bad:#be123c; }
* { box-sizing: border-box; }
body { margin:0; font-family: "Segoe UI", system-ui, -apple-system, Roboto, sans-serif; color:var(--ink); background:#f1f5f9; }
.ribbon { background:#fef3c7; color:#92400e; font-size:12px; text-align:center; padding:5px 12px; border-bottom:1px solid #fde68a; letter-spacing:.02em; }
header.top { background:linear-gradient(135deg,var(--brand),var(--brand-dark)); color:#fff; padding:18px 28px; display:flex; align-items:center; gap:14px; }
header.top .seal { width:42px; height:42px; border-radius:50%; background:rgba(255,255,255,.15); display:grid; place-items:center; font-weight:700; }
header.top h1 { font-size:20px; margin:0; font-weight:600; }
header.top p { margin:2px 0 0; font-size:12px; opacity:.8; }
main { max-width:860px; margin:24px auto; padding:0 16px 40px; }
.card { background:#fff; border:1px solid var(--line); border-radius:16px; box-shadow:0 1px 2px rgba(15,23,42,.05), 0 8px 24px rgba(15,23,42,.04); padding:24px; }
h2 { font-size:13px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:0 0 4px; }
h3 { font-size:22px; margin:0 0 16px; }
.steps { display:flex; gap:8px; margin:0 0 20px; padding:0; list-style:none; }
.steps li { flex:1; font-size:12px; color:var(--muted); border-top:3px solid var(--line); padding-top:6px; }
.steps li.on { color:var(--brand); border-color:var(--brand); font-weight:600; }
.row { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px; }
.btn { appearance:none; border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:10px; padding:9px 16px; font-size:14px; cursor:pointer; transition:.15s; }
.btn:hover { background:var(--soft); }
.btn-primary { background:var(--brand); border-color:var(--brand); color:#fff; }
.btn-primary:hover { background:var(--brand-dark); }
.btn-inverse { background:#fff; color:var(--brand); border-color:var(--brand); }
input[type=text] { width:100%; border:1px solid #cbd5e1; border-radius:10px; padding:11px 14px; font-size:15px; outline:none; }
input[type=text]:focus { border-color:var(--brand); box-shadow:0 0 0 3px rgba(30,78,140,.15); }
label.hint { display:block; font-size:12px; color:var(--muted); margin:14px 0 6px; }
#go { margin-top:14px; width:100%; padding:12px; font-size:15px; font-weight:600; }
#banner { margin-top:12px; color:var(--bad); font-size:14px; min-height:18px; }
#toast { position:fixed; top:14px; right:14px; max-width:320px; background:#0f172a; color:#fff; border-radius:10px; padding:0; font-size:13px; }
#toast:not(:empty) { padding:10px 14px; }
table { width:100%; border-collapse:collapse; font-size:14px; }
th { text-align:left; font-size:11px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); padding:8px 10px; border-bottom:2px solid var(--line); }
td { padding:9px 10px; border-bottom:1px solid var(--line); vertical-align:middle; }
.table-striped tbody tr:nth-child(odd) { background:#f8fafc; }
.table-striped tbody tr:hover { background:var(--soft); }
.btn-custom { padding:5px 14px; font-size:13px; }
.muted { color:var(--muted); font-size:12px; }
.status { font-size:12px; padding:2px 9px; border-radius:99px; background:#e2e8f0; }
.status.Active { background:#dcfce7; color:#166534; }
.status.Closed { background:#e2e8f0; color:#475569; }
.status.Warrant { background:transparent; }
.amount { font-size:34px; font-weight:700; color:var(--brand); margin:6px 0 14px; }
ul.charges { margin:8px 0 18px; padding-left:18px; font-size:14px; }
.g-recaptcha { display:flex; align-items:center; gap:12px; width:304px; margin-top:16px; padding:14px 16px; border:1px solid #d3d3d3; border-radius:4px; background:#f9f9f9; box-shadow:0 0 4px rgba(0,0,0,.08); cursor:pointer; }
.g-recaptcha .box { width:26px; height:26px; border:2px solid #c1c1c1; border-radius:3px; background:#fff; display:grid; place-items:center; font-size:18px; color:var(--ok); }
.g-recaptcha .text { font-size:14px; }
.g-recaptcha .brand { margin-left:auto; font-size:10px; color:#555; text-align:center; }
[hidden] { display:none !important; }
</style>
</head>
<body>
<div class="ribbon">Local replica of the court portal for demos and tests. No request leaves this computer.</div>
<header class="top"><div class="seal">CA</div><div><h1>Court Access Portal</h1><p>Superior Court of California, County of San Bernardino</p></div></header>
<main>
<div id="toast"></div>
<div class="card">
<ol class="steps"><li id="s1" class="on">Step 1 - Search</li><li id="s2">Step 2 - Select case</li><li id="s3">Step 3 - Select option</li></ol>
<div id="step1">
  <h2>Case payment search</h2>
  <h3>Find a case</h3>
  <div class="row">
    <button type="button" class="btn btn-default search-button btn-primary" id="case">Case Number</button>
    <button type="button" class="btn btn-default search-button" id="party">{{PARTY_LABEL}}</button>
  </div>
  <label class="hint" for="number">Last, First</label>
  <input id="number" type="text" placeholder="Last, First" autocomplete="off">
  <button type="submit" class="btn btn-primary" id="go">SEARCH</button>
  <div id="banner"></div>
  <div id="captcha" class="captcha-slot"></div>
</div>
<div id="step2" hidden>
  <h2>Search results</h2>
  <h3 id="found"></h3>
  <table class="table table-striped table-bordered"><thead><tr><th></th><th>Case</th><th>Name</th><th>Violation date</th><th>Status</th></tr></thead><tbody id="rows"></tbody></table>
  <div class="row" style="margin-top:16px"><button type="button" class="btn btn-inverse btn-custom again2">Search Again</button></div>
</div>
<div id="step3" hidden>
  <h2>Case payment options</h2>
  <h3 id="who"></h3>
  <div class="muted">Amount due</div><div class="amount" id="amount"></div>
  <div class="muted">Charges</div><ul class="charges" id="charges"></ul>
  <div class="row">
    <button type="button" class="btn btn-primary btn-custom" id="pay">Select</button>
    <button type="button" class="btn btn-inverse btn-custom again3">Search Again</button>
  </div>
</div>
</div>
</main>
<script>
let type = 'case';
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? '').replace(/[&<>"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function show(step) {
  for (const s of ['step1','step2','step3']) $(s).hidden = s !== step;
  for (const [i, s] of ['s1','s2','s3'].entries()) $(s).className = ('step' + (i + 1)) === step ? 'on' : '';
}
async function token() { return (await (await fetch('/api/traffic/token')).json()).token; }
function reset() { type = 'case'; $('case').classList.add('btn-primary'); $('party').classList.remove('btn-primary'); $('number').value=''; $('banner').textContent=''; show('step1'); }
function expired() { $('toast').textContent = 'Traffic Payment Session Expired. The page will be refreshed in 2 seconds.'; setTimeout(() => location.reload(), 150); }
function showCaptcha() {
  $('captcha').innerHTML = '<div class="g-recaptcha" role="checkbox" aria-checked="false"><div class="box"></div><div class="text">I am not a robot</div><div class="brand">protected by<br>CAPTCHA</div></div>';
  $('captcha').firstChild.onclick = async () => {
    $('captcha').firstChild.querySelector('.box').textContent = '\\u2713';
    await fetch('/api/replica/captcha-solved', {method:'POST'});
    setTimeout(() => { $('captcha').innerHTML = ''; }, 350);
  };
}
$('party').onclick = () => { type = 'parn'; $('party').classList.add('btn-primary'); $('case').classList.remove('btn-primary'); };
$('go').onclick = async () => {
  const t = await token();
  let body;
  try {
    const r = await fetch('{{SEARCH_PATH}}', {method:'POST', headers:{'Content-Type':'application/json','portal-token':t}, body: JSON.stringify({type, userMessage:'', value:$('number').value})});
    body = await r.json();
  } catch (e) { $('banner').textContent = 'The service is temporarily unavailable.'; return; }
  if (body.result === 1 && /expired/i.test(body.message)) return expired();
  if (body.result !== 0 || !body.data.length) { $('banner').textContent = 'No Case(s) Found'; return; }
  if (body.captcha) { showCaptcha(); return; }
  $('found').textContent = body.message || ('Found ' + body.data.length + ' Case(s)');
  $('rows').innerHTML = body.data.map((c) => '<tr><td>' + (c.caseStatus === 'Closed' ? '<span class="muted">NO ACTION AVAILABLE</span>' : '<button type="button" class="btn btn-primary btn-custom" data-case="' + esc(c['{{CASE_KEY}}']) + '">Select</button>') + '</td><td>' + esc(c['{{CASE_KEY}}']) + '</td><td>' + esc(c.caseCaption) + '</td><td>' + esc(c.fileDate) + '</td><td>' + (c.caseStatus === 'Warrant' ? '' : '<span class="status ' + esc(c.caseStatus) + '">' + esc(c.caseStatus) + '</span>') + '</td></tr>').join('');
  show('step2');
};
$('rows').onclick = async (e) => {
  const n = e.target.getAttribute && e.target.getAttribute('data-case'); if (!n) return;
  const t = await token();
  let body;
  try {
    body = await (await fetch('/api/traffic/select/' + n, {headers:{'portal-token':t}})).json();
  } catch (err) { $('toast').textContent = 'The service is temporarily unavailable.'; return; }
  if (body.result === 1) return expired();
  const d = body.data;
  $('who').textContent = (d.fullName || '') + ' | ' + (d.caseNumber || n);
  $('amount').textContent = '$' + String(d.bfAmount || '0.00').replace('$', '');
  $('charges').innerHTML = (d.charges || []).map((c) => '<li>' + esc(typeof c === 'string' ? c : (c.statute || '') + ' ' + (c.description || '')) + '</li>').join('');
  show('step3');
};
$('pay').onclick = () => fetch('/api/traffic/pay', {method:'POST'});
document.querySelector('.again2').onclick = reset; document.querySelector('.again3').onclick = reset;
</script>
</body></html>"""
