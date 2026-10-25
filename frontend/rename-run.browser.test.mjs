// Real App regression fixture; only synthetic annotation writes are accepted.
import './style.css';
const query = new URLSearchParams(location.search);
localStorage.setItem('simshelf-theme', query.get('theme') || 'system');
localStorage.setItem('simshelf-view', 'table');
location.hash = '#run/rename-fixture';
const mode = query.get('state') || 'running';
const active = ['running','stopping'].includes(mode);
const simulation = {id:'sim',name:'Rename experiment',root:'/disposable/source',
  entrypoint:'model.py',description:'',available:true,run_count:2,last_run:'2026-10-25T09:00:00Z',
  config:{output_dir:'outputs',source_include:['*.py'],source_exclude:[],rules:[],max_file_mb:25,max_run_mb:100}};
let record = {
  id:'rename-fixture',simulation_id:'sim',name:'Original experiment name',
  status:active ? 'running' : mode==='finalizing' ? 'completed' : mode,version:'1.0',started_at:'2026-10-25T09:00:00Z',
  ended_at:active ? null : '2026-10-25T09:01:00Z',duration:active ? null : 60,
  command:['/disposable/python','model.py','--seed','007',''],cwd:'/disposable/source',
  parameters:{seed:7},parameter_sources:{seed:'python'},notes:'Existing notes',tags:[],version_note:'',
  source_change:'same',snapshot_id:'source-hash',structure_id:'structure-hash',baseline_run_id:'rename-fixture',
  git:{commit:'abcdef',branch:'main',dirty:false},snapshot:{files:[{path:'model.py',size:12,blob:'source-hash'}]},
  environment:{python:'3.14',executable:'/disposable/python',platform:'Linux',source:'fixture',packages:[]},
  exit_code:active || mode==='interrupted' ? null : mode==='failed' ? 3 : 0,
  capture_root:'/disposable/source/outputs/run_fixed-id',capture_status:active || mode==='finalizing' ? 'pending' : 'complete',
  capture_counts:{copied:1,referenced:0,ignored:0,skipped:0,unchanged:0},capture_errors:[],source_warnings:[],
  can_stop:mode==='running' || mode==='stopping',stop_requested:mode==='stopping',
  artifacts:[],metrics:[],metric_count:0,annotation_history:[],
};
const other = {...record,id:'other-run',name:'Neighbor run',baseline_run_id:'other-run'};
const initialIdentity=JSON.stringify({...record,name:undefined,notes:undefined,annotation_history:undefined});
const requests=[];
let reject='',holdRead=false,held=null;
const response = (value,status=200) => Response.json(value,{status});
window.fetch=async(url,options={})=>{
  const path=new URL(url,location.origin).pathname;
  const method=options.method || 'GET', data=options.body ? JSON.parse(options.body) : null;
  requests.push({path,method,data});
  if (path==='/api/runs/rename-fixture' && method==='PATCH') {
    if (reject) {const message=reject;reject='';return response({detail:message},403);}
    if (data.name!==undefined && (!data.name.trim() || data.name.length>160)) return response({detail:'Use 1–160 characters.'},400);
    const history={...data,at:'2026-10-25T09:02:00Z',...(data.name===undefined ? {} : {previous_name:record.name})};
    record={...record,...data,annotation_history:[history,...record.annotation_history]};
    return response(record);
  }
  if (method!=='GET') throw Error('Unexpected fixture write '+method+' '+path);
  if (path==='/api/workspace') return response({path:'/disposable/library',version:'fixture',token:'fixture',schema_version:4});
  if (path==='/api/simulations') return response([simulation]);
  if (path==='/api/simulations/sim/preservation') return response({settings:null,status:{state:'not_configured',reason:'Not configured in fixture.'},global:{enabled:false}});
  if (path==='/api/runs') return response([record,other]);
  if (path==='/api/runs/rename-fixture') {
    if (holdRead) {
      holdRead=false;
      const stale=structuredClone(record);
      return new Promise(resolve=>{held=()=>resolve(response(stale));});
    }
    return response(record);
  }
  if (path==='/api/runs/other-run') return response(other);
  if (path.endsWith('/archive')) return response({events:[],pending:null,error:null,
    connection_status:{state:'disconnected'},preservation:{state:'not_enabled',events:0,annotations:0}});
  throw Error('Unmocked '+path);
};
const controls=document.createElement('aside');
controls.innerHTML='<button id="reject-save">Reject next save</button><button id="start-checks">Run regression checks</button><pre id="results" role="status"></pre>';
document.body.append(controls);
document.querySelector('#reject-save').onclick=()=>{reject='Refresh SimShelf before saving.';};
await import('./main');
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const assert=(ok,message)=>{if(!ok)throw Error(message);};
const button=text=>[...document.querySelectorAll('button')].find(e=>e.textContent.trim()===text);
const dialog=()=>document.querySelector('dialog[aria-labelledby="rename-run-title"]');
const input=()=>dialog()?.querySelector('input');
async function click(node){assert(node,'missing control');node.click();await wait(80);}
async function fill(value){
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input(),value);
  input().dispatchEvent(new Event('input',{bubbles:true}));await wait(20);
}
async function until(predicate){for(let i=0;i<100;i++){if(predicate())return;await wait(100);}throw Error('Timed out waiting for fixture state');}
const patchCount=()=>requests.filter(r=>r.method==='PATCH').length;
const title=()=>document.querySelector('.run-title-row h1')?.textContent;
async function runChecks(){
  const result=document.querySelector('#results');
  try {
    await until(()=>button('Rename run…'));
    assert(!button('Rename run…').disabled,mode+' can rename without completion/ownership gating');
    await click(button('Rename run…'));
    assert(input().value===record.name && document.activeElement===input(),'prefilled and focused');
    await fill('Canceled name');const writes=patchCount();
    await click(button('Cancel'));
    assert(patchCount()===writes && title()===record.name,'cancel has no write');
    assert(document.activeElement===button('Rename run…'),'cancel restores focus');
    await click(button('Rename run…'));await fill(' \t ');
    dialog().querySelector('form').requestSubmit();await wait(80);
    assert(dialog().querySelector('[role="alert"]') && input().getAttribute('aria-invalid')==='true','empty name error');
    assert(patchCount()===writes,'invalid name has no request');
    await fill('Rejected name');reject='Refresh SimShelf before saving.';
    dialog().querySelector('form').requestSubmit();await wait(80);
    assert(dialog() && dialog().textContent.includes('Refresh SimShelf'),'stale token error stays in dialog');
    assert(title()==='Original experiment name','failed write preserves confirmed title');
    assert(input().value==='Rejected name' && document.activeElement===input(),'failed write keeps draft and focus');
    await fill('Confirmed renamed experiment');
    await wait(3200);assert(input().value==='Confirmed renamed experiment','polling cannot erase dialog draft');
    holdRead=true;await until(()=>held!==null); // A real polling read captures the old name.
    dialog().querySelector('form').requestSubmit();await until(()=>!dialog());
    assert(title()===record.name && record.name==='Confirmed renamed experiment','confirmed rename updates title');
    held();held=null;await wait(100);
    assert(title()===record.name,'late polling response cannot undo save');
    await wait(3200);assert(title()===record.name,'fresh polls preserve rename');
    assert(document.activeElement===button('Rename run…'),'save restores action focus');
    await click(button('Notes'));
    assert(![...document.querySelectorAll('label')].some(e=>e.textContent.trim()==='Run name'),'notes has no stale name draft');
    await click(button('Save notes'));
    assert(requests.filter(r=>r.method==='PATCH').at(-1).data.name===undefined,'notes cannot overwrite renamed title');
    assert(title()===record.name,'notes retains confirmed name');
    await click(button('← Back to runs'));await until(()=>[...document.querySelectorAll('.run-link')].some(e=>e.textContent.includes('Confirmed renamed experiment')));
    const renamed=[...document.querySelectorAll('.run-link')].find(e=>e.textContent.includes(record.name));
    assert(renamed,'listing updates without reload');await click(renamed);
    await until(()=>title()===record.name);
    assert(JSON.stringify({...record,name:undefined,notes:undefined,annotation_history:undefined})===initialIdentity,'execution and source identity unchanged');
    result.textContent='PASS '+mode+': cancel, validation, rejection, focus, polling, notes, list and navigation';
  } catch(error){result.textContent='FAIL '+mode+' '+error.stack;}
}
document.querySelector('#start-checks').onclick=runChecks;
if(query.has('test'))runChecks();
