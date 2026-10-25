// Real launch components with synthetic API responses; no process is executed.
import React, {act} from 'react';
import {createRoot} from 'react-dom/client';
import {LaunchSimulation} from './LaunchSimulation';
import './style.css';

globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const root = createRoot(document.querySelector('#root'));
const results = document.querySelector('#results');
const requests = [];
let schema = 4, key = 0;
const interpreter = '/disposable/python';
const simulation = {id:'auto',name:'Progress fixture',root:'/disposable/source',
  entrypoint:'model.py',config:{output_dir:'outputs'}};
const execution = {interpreter,cwd:'.',arguments:[],output_dir:'outputs'};
const review = {output_path:'/disposable/source/outputs',requires_acknowledgement:false,targets:[]};
window.fetch = async (url, options = {}) => {
  const path = new URL(url, location.origin).pathname;
  const data = options.body ? JSON.parse(options.body) : null;
  requests.push({path,method:options.method || 'GET',data});
  let value;
  if (path.endsWith('/workspace')) value = {schema_version:schema};
  else if (path.endsWith('/progress/enable')) {
    if (data.confirmed !== true) throw Error('missing explicit consent');
    schema = 4; value = {schema_version:schema};
  } else if (path.endsWith('/parameters')) value = {
    parameters:[],warnings:[],source:'none',fingerprint:null,
    output_policy:{state:'absent',launcher_allowed:true,reason:'No SWSS metadata.'}};
  else if (path.endsWith('/interpreters')) value = {candidates:[]};
  else if (path.endsWith('/execution/outputs')) value = review;
  else if (path.endsWith('/execution/validate')) value = {
    output_review:review,command:[interpreter,'model.py'],cwd:simulation.root,
    output_path:review.output_path,validation:{version:'3.14',message:'Fixture only'}};
  else if (path.endsWith('/execution')) value = {};
  else throw Error('Unexpected request '+path);
  return new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
};
const assert = (ok, message) => {if (!ok) throw Error(message);};
const button = text => [...document.querySelectorAll('button')].find(e=>e.textContent.trim()===text);
const select = () => document.querySelector('.progress-settings select');
const settle = () => act(async()=>{await new Promise(resolve=>setTimeout(resolve,400));});
async function click(node) {assert(node,'missing button');await act(async()=>node.click());await settle();}
async function setValue(node, value, type) {
  await act(async()=>{
    Object.getOwnPropertyDescriptor(type.prototype,'value').set.call(node,value);
    node.dispatchEvent(new Event(type === HTMLSelectElement ? 'change' : 'input',{bubbles:true}));
  });
  await settle();
}
async function mount(saved, version=4) {
  schema=version; requests.length=0;
  await act(async()=>root.render(React.createElement(LaunchSimulation,{
    key:++key,simulation:{...simulation,...(saved ? {execution:saved} : {})},
    saved(){},done(){throw Error('No launch allowed');},
  })));
  await settle();
  await setValue(document.querySelector('.interpreter-picker input'),interpreter,HTMLInputElement);
  await click([...document.querySelectorAll('input[type="checkbox"]')].find(e=>e.parentElement.textContent.includes('Use manual argv')));
}
async function save(expected) {
  await click(button('Save settings'));
  const saved = requests.filter(r=>r.method==='PUT').at(-1);
  assert(saved?.data.progress_mode === expected,'saved mode '+expected);
  assert(!button('Start simulation').disabled,'validated launch available');
}
async function run() {
  const passed=[];
  async function check(name, fn) {await fn();passed.push(name);results.textContent=passed.map(n=>'PASS '+n).join('\n');}
  await check('fresh settings default to auto without executing or migrating',async()=>{
    await mount();
    assert(select().value==='auto' && !select().disabled,'fresh auto default');
    assert(!requests.some(r=>r.method!=='GET' && !r.path.endsWith('/execution/outputs')),'passive setup');
    await save('auto');
    await setValue(select(),'percent',HTMLSelectElement);
    assert(button('Start simulation').disabled,'mode change invalidates validation');
    await save('percent');
  });
  for (const mode of ['off','step','percent','auto',undefined]) {
    await check('saved '+(mode || 'legacy missing')+' mode retained',async()=>{
      await mount({...execution,...(mode ? {progress_mode:mode} : {})});
      assert(select().value===(mode || 'off'),'existing mode retained');
      await save(mode || 'off');
    });
  }
  await check('fresh older library launches off; explicit enable activates auto',async()=>{
    await mount(undefined,3);
    assert(select().disabled,'schema gate');
    await save('off');
    assert(!requests.some(r=>r.path.endsWith('/progress/enable')),'no implicit enable');
    await click(button('Enable progress reporting…'));
    const confirm=button('Enable progress reporting for this library');
    assert(confirm.disabled,'backup confirmation required');
    await click(button('Cancel'));
    assert(!requests.some(r=>r.path.endsWith('/progress/enable')),'cancel leaves schema alone');
    await click(button('Enable progress reporting…'));
    await click(document.querySelector('[aria-label="Enable progress reporting confirmation"] input'));
    await click(button('Enable progress reporting for this library'));
    assert(schema===4 && select().value==='auto' && !select().disabled,'explicit enable retains fresh default');
    assert(button('Start simulation').disabled,'enable invalidates off validation');
    await save('auto');
  });
  assert(!requests.some(r=>r.path.endsWith('/launch')),'no process launch');
  results.textContent+='\nALL '+passed.length+' PASSED';
}
run().catch(error=>{results.textContent+='\nFAIL '+error.stack;});
