// Disposable real-DOM regression harness. Network responses are immutable fixtures.
import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { SourceComparison } from './SourceComparison';
import './style.css';
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const root = createRoot(document.querySelector('#root'));
const results = document.querySelector('#results');
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const assert = (ok, message) => { if (!ok) throw Error(message); };
const base = {
  run_id:'current', version:'0.3.1', recorded_change:'changed', snapshot_id:'b'.repeat(64),
  baseline:{id:'baseline-record',version:'0.3.1',snapshot_id:'a'.repeat(64),started_at:'2026-10-25T00:00:00Z',deleted:true},
  counts:{added:1,removed:1,changed:1,unchanged:1}, total:3, offset:0, limit:100,
  notes:['Baseline includes a removed path inside this run’s recorded output exclusions; historical evidence is unchanged.'],
  selection_changes:[{field:'output_dirs',before:['outputs'],after:['results']}],
  changes:[
    {path:'results/old/model.py',change:'removed',classification:'python',before:{blob:'a'.repeat(64),size:10,mode:420},after:null,permissions_changed:false,output_boundary:'results',output_boundary_confirmed:true},
    {path:'settings.json',change:'changed',classification:'non-python',before:{blob:'b'.repeat(64),size:1,mode:420},after:{blob:'c'.repeat(64),size:2,mode:493},permissions_changed:true,output_boundary:null},
    {path:'<img src=x onerror=alert(1)>.py',change:'added',classification:'python',before:null,after:{blob:'d'.repeat(64),size:0,mode:420},permissions_changed:false,output_boundary:null},
  ],
};
let fail=false, large=false, held=false, pending=[], requests=[], selected=[];
const errors=[];
const originalError=console.error;
console.error=(...args)=>{errors.push(args.join(' '));originalError(...args);};
window.fetch=async url=>{
  requests.push(url);
  if (held) return new Promise(resolve=>pending.push(resolve));
  if (fail) return new Response(JSON.stringify({detail:'Fixture manifest integrity failure'}),{status:400});
  const offset=Number(new URL(url,location.origin).searchParams.get('offset'));
  return new Response(JSON.stringify({...base,run_id:url.split('/')[3],total:large?101:3,offset,
    changes:offset?[{...base.changes[0],path:'last.py'}]:base.changes}),{headers:{'Content-Type':'application/json'}});
};
let instance=0;
async function mount(id='current') {
  await act(async()=>{root.render(React.createElement(SourceComparison,{key:++instance,runId:id,selectPath:path=>selected.push(path)}));});
  await act(async()=>{await wait(10);});
}
async function click(name) {
  await act(async()=>{[...document.querySelectorAll('button')].find(b=>b.textContent===name).click();await wait(10);});
  await act(async()=>{await wait(10);});
}
const passed=[];
async function check(name,fn){await fn();passed.push(name);results.textContent=passed.map(n=>'PASS '+n).join('\n');}
async function tests(){
  passed.length=0;errors.length=0;
  await check('canonical baseline, removed paths and selection evidence remain explicit',async()=>{
    await mount();
    assert(document.body.innerText.includes('baseline-record')&&document.body.innerText.includes('run removed; snapshot retained'),'canonical identity');
    assert(document.body.innerText.includes('1 added · 1 removed · 1 changed · 1 unchanged'),'counts');
    assert(!document.querySelector('img'),'paths render as plain text');
    await click('results/old/model.py');assert(selected.at(-1)==='results/old/model.py','baseline-only path selectable');
    assert(document.body.innerText.includes('Non-Python file'),'whole snapshot, not entrypoint only');
  });
  await check('pagination clears old paths and returns to the original page',async()=>{
    large=true;await mount();await click('Next changed paths');
    assert(document.body.innerText.includes('last.py')&&!document.body.innerText.includes('settings.json'),'next page');
    await click('Previous changed paths');assert(document.body.innerText.includes('settings.json'),'previous page');large=false;
  });
  await check('failure reports evidence limits and retry recovers',async()=>{
    fail=true;await mount();assert(document.body.innerText.includes('Fixture manifest integrity failure'),'specific error');
    assert(!document.body.innerText.includes('settings.json'),'no stale success');
    fail=false;await click('Retry source comparison');assert(document.body.innerText.includes('settings.json'),'retry');
  });
  await check('late old-run responses cannot replace the new run',async()=>{
    held=true;await mount('old-run');assert(document.body.innerText.includes('Loading recorded source comparison'),'loading state');
    held=false;await mount('new-run');
    await act(async()=>{for(const resolve of pending)resolve(new Response(JSON.stringify({...base,baseline:{...base.baseline,id:'STALE BASELINE'}})));pending=[];await wait(10);});
    assert(!document.body.innerText.includes('STALE BASELINE'),'late response discarded');
    assert(requests.some(url=>url.includes('/new-run/')),'new run loaded');
  });
  assert(errors.length===0,errors.join('\n'));
  assert(document.documentElement.scrollWidth<=innerWidth,'no horizontal overflow');
  results.textContent+='\n'+passed.length+' passed; no console errors.';
}
document.querySelector('#run-tests').onclick=()=>tests().catch(error=>{results.textContent+='\nFAIL '+error.stack;});
await mount();
