import {test} from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {ParameterHint} from './ParameterHint.tsx';
import {parameterRows, rowArguments, parameterError, missingRequiredRows} from './parameterRows.ts';
const base={name:'--N',flags:['--N','-n'],help:'float · Default: authored help <unchanged>',type:'int',action:'store',required:false,supported:true,choices:null,default_known:false,default:null};
const render=(p,token=p.name,value=null,enabled=false)=>renderToStaticMarkup(React.createElement(ParameterHint,{parameter:p,token,value,enabled,id:'hint'}));
test('authored help is separate and preserved; unknown defaults add no mandatory meaning or generated type',()=>{
 const html=render(base);
 assert.match(html, /class="parameter-help">float · Default: authored help &lt;unchanged&gt;<\/span>/);
 assert.match(html, /class="parameter-metadata">Aliases: -n<\/span>/);
 assert.doesNotMatch(html,/required|\bint\b/);
 const rows=parameterRows([], [base]);
 assert.deepEqual(rowArguments(rows),[]);assert.equal(parameterError(rows,[base]),'');assert.deepEqual(missingRequiredRows(rows),[]);
});
test('known zero false empty string and int64 defaults remain explicit hints, with legible choices',()=>{
 for(const [type,value,expected] of [['int',0,'0'],['int','9223372036854775807','9223372036854775807'],['str','','&quot;&quot;'],['bool',false,'false']]){
  const p={...base,type,default_known:true,default:value,help:''};
  assert.ok(render(p,p.name,'custom').includes(`Default: ${expected}`));
  assert.deepEqual(rowArguments(parameterRows([], [p])),[]);
 }
 const html=render({...base,type:'str',default_known:true,default:'A',choices:['A',''],help:''},'-n');
 assert.match(html,/Aliases: --N/);assert.match(html,/Choices: &quot;A&quot;, &quot;&quot;/);
 assert.doesNotMatch(html,/parameter-help/);
});
test('metadata rendering does not mutate mixed exact argv, disabled drafts or required flag semantics',()=>{
 const flag={...base,name:'--confirm',flags:['--confirm'],type:'bool',action:'store_false',required:true};
 const label={...base,name:'--label',flags:['--label'],type:'str'};
 const args=['-n','00192','--N=00192','--label=','--unknown','','--','--confirm'];
 const rows=parameterRows(args,[base,flag,label]);
 const draft=rows.find(r=>r.parameter?.name===flag.name&&!r.enabled);draft.valueOpen=false;
 const before=JSON.stringify(rows);
 for(const row of rows)if(row.parameter)render(row.parameter,row.token);
 assert.equal(JSON.stringify(rows),before);assert.deepEqual(rowArguments(rows),args);
 assert.equal(missingRequiredRows(rows).length,1);
 assert.match(render(flag),/Sets false when enabled/);assert.doesNotMatch(render(flag),/Aliases:/);
 const reopened=parameterRows(JSON.parse(JSON.stringify(rowArguments(rows))),[base,flag,label],rows);
 assert.deepEqual(rowArguments(reopened),args);
});

test('default visibility follows edits/restoration and actual declared defaults, independent of enabled state',()=>{
 const p={...base,help:'',default_known:true,default:100};
 for(const enabled of [false,true]) {
  assert.doesNotMatch(render(p,p.name,'00100',enabled), /Default:/);
  assert.match(render(p,p.name,'101',enabled), /Default: 100/);
  assert.doesNotMatch(render(p,p.name,'+100',enabled), /Default:/);
 }
 const rows=parameterRows(['-n','101'],[p]);
 assert.match(render(p,rows[0].token,rows[0].value,rows[0].enabled), /Default: 100/);
 rows[0].enabled=false;
 const before=JSON.stringify(rows);
 render(p,rows[0].token,rows[0].value,rows[0].enabled);
 assert.equal(JSON.stringify(rows),before);assert.deepEqual(rowArguments(rows),[]);
 rows[0].enabled=true;assert.deepEqual(rowArguments(rows),['-n','101']);
});
test('unknown and explicit empty defaults remain distinct without generated placeholder descriptions',()=>{
 const unknown={...base,help:'',flags:['--N']};
 assert.doesNotMatch(render(unknown),/parameter-help|parameter-metadata|unknown|Default:/);
 const empty={...unknown,type:'str',default_known:true,default:''};
 assert.doesNotMatch(render(empty,empty.name,''),/Default:/);
 assert.doesNotMatch(render(empty,empty.name,null),/Default:/);
 assert.match(render(empty,empty.name,'custom'),/Default: &quot;&quot;/);
 assert.doesNotMatch(render({...empty,default:'x'},empty.name,'x'),/Default:/);
});
test('numeric equality preserves int64 and precise decimals without normalizing argv',()=>{
 for(const [type,def,equal,different] of [
  ['int','9223372036854775807','+09223372036854775807','9223372036854775806'],
  ['float',0.01,'1e-2','0.0100000000000000001'],
  ['float',0,'-0.0e99','1e-9999'],
  ['float',1,'10e-1','1.0000000000000001'],
 ]) {
  const p={...base,help:'',type,default_known:true,default:def};
  assert.doesNotMatch(render(p,p.name,equal),/Default:/);
  assert.match(render(p,p.name,different),/Default:/);
  const rows=parameterRows([p.name,equal],[p]);
  render(p,p.name,rows[0].value,true);assert.deepEqual(rowArguments(rows),[p.name,equal]);
 }
 for(const value of ['', ' ', 'NaN', 'Infinity', 'invalid'])assert.match(render({...base,help:'',type:'float',default_known:true,default:0},base.name,value),/Default:/);
});
test('flags retain action metadata and compare only the deliberately enabled action',()=>{
 const p={...base,help:'',type:'bool',action:'store_false',default_known:true,default:false};
 assert.doesNotMatch(render(p,p.name,null,true),/Default:/);
 assert.doesNotMatch(render(p,p.name,null,false),/Default:/);
 assert.match(render({...p,default:true},p.name,null,true),/Default: true/);
 assert.match(render(p,p.name,null,true),/Sets false when enabled/);
});

test('unset, explicit equal/different and restored optional drafts have independent footer and argv semantics',()=>{
 const p={...base,help:'',type:'str',default_known:true,default:'baseline'};
 for(const enabled of [false,true]) {
  const row={...parameterRows([], [p])[0],enabled};
  for(const [value,show] of [[null,false],['baseline',false],['custom',true],['',true],['baseline',false],[null,false]]) {
   row.value=value;
   const before=JSON.stringify(row), args=rowArguments([row]);
   const html=render(p,row.token,row.value,row.enabled);
   assert.equal(html.includes('Default:'),show);
   assert.equal(JSON.stringify(row),before);
   assert.deepEqual(rowArguments([row]),args);
   if(!enabled)assert.deepEqual(args,[]);
   else assert.deepEqual(args,value===null?[p.name]:[p.name+'='+value]);
   assert.doesNotMatch(render({...p,default_known:false},row.token,value,enabled),/Default:/);
  }
 }
});
