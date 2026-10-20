import {test} from 'node:test';
import assert from 'node:assert/strict';
import {parameterRows, rowArguments} from './parameterRows.ts';
import {parameterPresentation} from './parameterPresentation.ts';
const p = {name:'--dt',flags:['--dt','-d'],help:'Integration time increment',type:'float',action:'store',required:false,supported:true,choices:null,default_known:true,default:0.1};
const flag = {...p,name:'--no-plots',flags:['--no-plots'],action:'store_false',type:'bool'};
test('search matches names aliases help and types case insensitively, with counts and no matches',()=>{
 const rows=parameterRows(['--unknown',''],[p,flag]);
 for(const term of ['--dt','-d','INTEGRATION time','float']) assert.equal(parameterPresentation(rows,term).matches,term==='-d'||term==='--dt'||term==='float'?1:2);
 const empty=parameterPresentation(rows,'unmatched');
 assert.equal(empty.total,2);assert.equal(empty.matches,0);
 assert.equal(empty.sections.length,1);assert.equal(empty.sections[0].rows[0].row.token,'--unknown');
 assert.equal(parameterPresentation(rows,'  ').matches,2);
});
test('required presentation comes first without changing exact argv or original edit indexes',()=>{
 const required={...p,name:'--label',flags:['--label'],type:'str',required:true};
 const args=['--no-plots','--dt=1e-3','--label','','--other','x','--','--dt=2'];
 const rows=parameterRows(args,[p,flag,required]);
 const view=parameterPresentation(rows,'');
 assert.equal(view.sections[0].name,'Required arguments');
 assert.equal(view.sections[0].rows[0].index,2);
 for(const section of view.sections) for(const {row,index} of section.rows) assert.equal(row,rows[index]);
 assert.deepEqual(rowArguments(rows),args);
 assert.ok(!parameterPresentation(parameterRows([], [p,flag]),'').sections.some(s=>s.name==='Required arguments'));
});
test('filtering preserves enabled and disabled drafts, aliases repeats delimiters and numeric spelling',()=>{
 const args=['-d','1e-3','--dt=1e-3','--unknown','','--','tail'];
 const rows=parameterRows(args,[p,flag]);
 const index=rows.findIndex(r=>r.parameter?.name===flag.name);
 rows[index].enabled=true;
 const expected=rowArguments(rows), before=JSON.stringify(rows);
 for(const query of ['plots','none','required','']) {
  const view=parameterPresentation(rows,query);
  assert.equal(JSON.stringify(rows),before);assert.deepEqual(rowArguments(rows),expected);
  assert.ok(view.sections.at(-1).rows.some(r=>r.row.token==='-d'));
 }
 rows[index].enabled=false;rows[index].value=null;
 parameterPresentation(rows,'none');assert.equal(rows[index].enabled,false);
});
test('77 declarations remain searchable without losing an edited hidden value',()=>{
 const parameters=Array.from({length:77},(_,i)=>({...p,name:`--parameter-${i}`,flags:[`--parameter-${i}`,`--alias-${i}`],help:`Diagnostic ${i}`,action:i%5===0?'store_true':'store'}));
 const rows=parameterRows([],parameters);
 const {index}=parameterPresentation(rows,'--alias-31').sections[0].rows[0];
 rows[index].enabled=true;rows[index].value='00192';
 const expected=['--parameter-31=00192'];
 assert.equal(parameterPresentation(rows,'unmatched').matches,0);
 assert.deepEqual(rowArguments(rows),expected);
 assert.equal(parameterPresentation(rows,'').matches,77);
 assert.equal(parameterPresentation(rows,'--alias-31').sections[0].rows[0].row.value,'00192');
 rows[index].enabled=false;
 parameterPresentation(rows,'other');assert.equal(rows[index].value,'00192');
 assert.deepEqual(rowArguments(rows),[]);
});
test('required flags stay distinct in semantics and unsupported/repeated declarations remain manual',()=>{
 const requiredFlag={...flag,required:true};
 const unsupported={...p,name:'--custom',flags:['--custom'],supported:false};
 const rows=parameterRows(['--custom','value','--dt=1','--dt=1'],[p,requiredFlag,unsupported]);
 const view=parameterPresentation(rows,'');
 assert.equal(view.sections[0].name,'Required arguments');
 assert.equal(view.sections[0].rows[0].row.parameter.action,'store_false');
 assert.equal(view.sections.at(-1).rows.length,3);
 assert.equal(view.total,1);
 assert.deepEqual(rowArguments(rows),['--custom','value','--dt=1','--dt=1']);
});
test('inline human-readable types remain searchable without changing argv',()=>{
 const rows=parameterRows([], [{...p,help:'',type:'int'}, {...p,help:'',name:'--label',flags:['--label'],type:'str'}]);
 for(const term of ['int','integer','str','string']) assert.equal(parameterPresentation(rows,term).matches,1);
 assert.deepEqual(rowArguments(rows),[]);
});
