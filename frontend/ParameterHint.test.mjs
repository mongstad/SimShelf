import {test} from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {ParameterHint} from './ParameterHint.tsx';
import {parameterRows, rowArguments, parameterError, missingRequiredRows} from './parameterRows.ts';
const base={name:'--N',flags:['--N','-n'],help:'float · Default: authored help <unchanged>',type:'int',action:'store',required:false,supported:true,choices:null,default_known:false,default:null};
const render=(p,token=p.name)=>renderToStaticMarkup(React.createElement(ParameterHint,{parameter:p,token,id:'hint'}));
test('authored help is separate and preserved; unknown defaults add no mandatory meaning or generated type',()=>{
 const html=render(base);
 assert.match(html, /class="parameter-help">float · Default: authored help &lt;unchanged&gt;<\/span>/);
 assert.match(html, /class="parameter-metadata">Aliases: -n · Declared default: unknown<\/span>/);
 assert.doesNotMatch(html,/required|\bint\b/);
 const rows=parameterRows([], [base]);
 assert.deepEqual(rowArguments(rows),[]);assert.equal(parameterError(rows,[base]),'');assert.deepEqual(missingRequiredRows(rows),[]);
});
test('known zero false empty string and int64 defaults remain explicit hints, with legible choices',()=>{
 for(const [type,value,expected] of [['int',0,'0'],['int','9223372036854775807','9223372036854775807'],['str','','&quot;&quot;'],['bool',false,'false']]){
  const p={...base,type,default_known:true,default:value,help:''};
  assert.ok(render(p).includes(`Declared default (hint): ${expected}`));
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
