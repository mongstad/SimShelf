// Real React/DOM regression fixture. Bundle with esbuild and serve externally.
// HTML needs #root, #results and a #run-tests button. No simulation is executed.
import React, {act} from 'react';
import {createRoot} from 'react-dom/client';
import {ArgumentEditor} from './ArgumentEditor';
import './style.css';

globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const root = createRoot(document.querySelector('#root'));
const results = document.querySelector('#results');
const discovery = await (await fetch('./discovery.json')).json();
window.fetch = async () => new Response(JSON.stringify(discovery),
  {headers:{'Content-Type':'application/json'}});
const assert = (ok, message) => { if (!ok) throw Error(message); };
let key=0, initial=[], argv=[], summary='';
const search = () => document.querySelector('input[type="search"]');
async function mount(args) {
  key++;initial=args;argv=[...args];
  await act(async()=>root.render(React.createElement(ArgumentEditor, {
    key,initial,simulationId:'fixture',entry:'sim.py',
    change: next=>{argv=next;}, validation:error=>{summary=error;}, reviewed(){},pasteEditing(){},
  })));
  await act(async()=>{await new Promise(resolve=>setTimeout(resolve,30));});
}
async function click(node) {await act(async()=>node.click());}
async function fill(node,text) {
  await act(async()=>{
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(node,text);
    node.dispatchEvent(new Event('input',{bubbles:true}));
  });
}
const same = expected => assert(JSON.stringify(argv)===JSON.stringify(expected),'exact argv: '+JSON.stringify(argv));
async function run() {
  const passed=[];
  async function check(name,fn) {await fn();passed.push(name);results.textContent=passed.map(n=>'PASS '+n).join('\n');}
  await check('saved shorter flag retains all 22 schema-3 controls and searchable interval',async()=>{
    await mount(['--volume']);
    assert(document.body.textContent.includes('22 declared controls.'),'22 controls');
    await fill(search(),'volume');
    assert(document.body.textContent.includes('2 of 22 declared controls match.'),'two volume matches');
    assert(document.querySelector('[aria-label="Value for --volume-interval"]'),'interval control');
    same(['--volume']);
    await fill(search(),'interval');
    assert(document.body.textContent.includes('1 of 22 declared controls match.'),'interval match');
  });
  await check('explicit edit emits exact preview and survives rescan and reopening',async()=>{
    await click(document.querySelector('[aria-label="Enable --volume-interval"]'));
    await fill(document.querySelector('[aria-label="Value for --volume-interval"]'),'0.1');
    const expected=['--volume','--volume-interval=0.1'];same(expected);
    assert(summary==='','valid editor launch arguments');
    await click([...document.querySelectorAll('button')].find(b=>b.textContent==='Rescan parameters'));
    same(expected);
    await mount(expected);await fill(search(),'volume');same(expected);
    assert(document.querySelector('[aria-label="Value for --volume-interval"]').value==='0.1','restored value');
  });
  await check('reverse order preserves separate numeric spelling',async()=>{
    const args=['--volume-interval','1e-1','--volume'];await mount(args);
    await fill(search(),'volume');same(args);
    assert(document.body.textContent.includes('2 of 22 declared controls match.'),'both controls');
    await fill(document.querySelector('[aria-label="Value for --volume-interval"]'),'0.01');
    same(['--volume-interval','0.01','--volume']);
  });
  await check('disabled shorter flag does not insert any default',async()=>{
    await mount([]);await fill(search(),'volume');same([]);
    assert(document.body.textContent.includes('2 of 22 declared controls match.'),'both disabled controls');
  });
  results.textContent+='\nALL '+passed.length+' PASSED';
}
document.querySelector('#run-tests').onclick=()=>run().catch(e=>{results.textContent+='\nFAIL '+e.stack;});
