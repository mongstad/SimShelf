// Real React/DOM regression fixture. Bundle with esbuild and serve externally.
// HTML needs #root, #results and a #run-tests button. No simulation is executed.
import React, {act} from 'react';
import {createRoot} from 'react-dom/client';
import {ArgumentEditor} from './ArgumentEditor';
import './style.css';

globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const root = createRoot(document.querySelector('#root'));
const results = document.querySelector('#results');
const p = {name:'--rate',flags:['--rate','-r'],type:'float',action:'store',
  required:true,supported:true,choices:null,default_known:true,default:0.1,help:'Rate'};
const flag = {...p,name:'--quiet',flags:['--quiet'],type:'bool',action:'store_true'};
const parameters = [p,flag];
window.fetch = async () => new Response(JSON.stringify({parameters, fingerprint:'fixture',
  provenance:{binding_status:'unverified'}, warnings:[],source:'swss.toml'}),
  {headers:{'Content-Type':'application/json'}});
const assert = (ok, message) => { if (!ok) throw Error(message); };
let key=0, attempt=0, initial=[], argv=[], summary='';
const group = name => [...document.querySelectorAll('.parameter-disclosure')].find(e => e.textContent.includes(name));
const value = () => document.querySelector('[aria-label="Value for --rate"]');
const search = () => document.querySelector('input[type="search"]');
async function render() {
  await act(async () => { root.render(React.createElement(ArgumentEditor, {
    key,initial,simulationId:'fixture',entry:'sim.py',validationAttempt:attempt,
    change: next => {argv=next;},validation: error => {summary=error;},
    reviewed() {},pasteEditing() {},
  })); });
}
async function mount(args) {key++;attempt=0;initial=args;argv=[...args];await render();await act(async()=>{await new Promise(resolve=>setTimeout(resolve,30));});}
async function click(node) {await act(async()=>node.click());}
async function fill(node,text) {
  await act(async()=>{
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(node,text);
    node.dispatchEvent(new Event('input',{bubbles:true}));
  });
}
async function validate() {attempt++;await render();}
function focusedControl(node) {
  assert(document.activeElement===node,'offending control receives focus');
  assert(!node.closest('[hidden]'),'offending control is revealed');
  assert(node.getAttribute('aria-invalid')==='true','control marked invalid');
  const ids=node.getAttribute('aria-describedby').split(' ');
  assert(ids.some(id=>document.getElementById(id)?.textContent===summary),'error associated with control');
}
async function run() {
  const passed=[];
  async function check(name,fn) {await fn();passed.push(name);results.textContent=passed.map(n=>'PASS '+n).join('\n');}
  await check('omitted required values and flags open both collections and focus value',async()=>{
    await mount([]);await validate();focusedControl(value());
    assert(group('Flags').getAttribute('aria-expanded')==='true','missing flag revealed');
    assert(JSON.stringify(argv)==='[]','omissions unchanged');
  });
  for(const args of [['--rate=','--quiet'],['-r','NaN','--quiet'],['--rate=Infinity','--quiet']]) {
    await check('invalid supplied '+JSON.stringify(args),async()=>{
      await mount(args);await validate();focusedControl(value());
      assert(summary==='--rate needs a finite number.','accepted validator message');
      assert(JSON.stringify(argv)===JSON.stringify(args),'exact supplied argv retained');
    });
  }
  await check('search cannot hide error; repeated validation reopens and refocuses',async()=>{
    await mount(['--rate=','--quiet','--unknown','','--','-r','00192']);
    const before=JSON.stringify(argv);
    await fill(search(),'unmatched');await validate();focusedControl(value());
    assert(search().value==='','search cleared');
    for(let i=0;i<2;i++) {
      await click(group('Parameters'));group('Parameters').focus();await validate();focusedControl(value());
    }
    assert(JSON.stringify(argv)===before,'filter/repeated validation preserves argv');
    await fill(value(),'1e-3');assert(!value().hasAttribute('aria-invalid'),'correction clears inline error');
  });
  await check('missing required flag receives focus after valid value',async()=>{
    await mount(['-r','00192']);await fill(search(),'rate');await validate();
    focusedControl(document.querySelector('[aria-label="Enable --quiet"]'));
    assert(search().value==='','flag search cleared');
    assert(JSON.stringify(argv)==='["-r","00192"]','alias and spelling retained');
  });
  results.textContent+='\nALL '+passed.length+' PASSED';
}
document.querySelector('#run-tests').onclick=()=>run().catch(e=>{results.textContent+='\nFAIL '+e.stack;});
