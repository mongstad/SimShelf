import {test} from 'node:test';
import assert from 'node:assert/strict';
import {parameterRows, rowArguments, parameterError, missingRequiredRows, invalidParameterRows} from './parameterRows.ts';
import {parameterPresentation} from './parameterPresentation.ts';
const value = name => ({name, flags:[name], action:'store', type:'float', supported:true,
  required:false, choices:null, default_known:true, default:1});
const volume = {...value('--volume'), type:'bool', action:'store_true'};
const interval = value('--volume-interval');
const controls = rows => rows.filter(r=>r.parameter && !r.manual);

test('prefix pairs retain distinct controls across saved argv, search, edit and rescan',()=>{
  for (const short of [volume, value('--volume')]) {
    const parameters=[short,interval];
    const shortArgs=short.action==='store' ? ['--volume','001.0'] : ['--volume'];
    for (const args of [[],shortArgs,['--volume-interval=0.1'],
      [...shortArgs,'--volume-interval=0.1'],['--volume-interval','1e-1',...shortArgs]]) {
      let rows=parameterRows(args,parameters);
      assert.equal(controls(rows).length,2);
      assert.deepEqual(rowArguments(rows),args);
      assert.equal(parameterPresentation(rows,'volume').matches,2);
      assert.equal(parameterPresentation(rows,'interval').matches,1);
      assert.equal(parameterPresentation(rows,'').total,2);
      rows=parameterRows(JSON.parse(JSON.stringify(rowArguments(rows))),parameters,rows);
      assert.equal(controls(rows).length,2);
      assert.deepEqual(rowArguments(rows),args);
      const target=rows.find(r=>r.parameter?.name===interval.name);
      target.enabled=true;target.value='0.01';
      const expected=target.equals ? '--volume-interval=0.01' : '--volume-interval';
      assert.ok(rowArguments(rows).includes(expected));
      assert.equal(parameterError(rows,parameters),'');
      rows=parameterRows(rowArguments(rows),parameters,rows);
      assert.equal(controls(rows).length,2);
    }
  }
});

test('exact names and aliases beat prefixes for equals and separate values in either order',()=>{
  const foo={...value('--foo'),flags:['--foo','--f']}, bar=value('--foobar');
  for(const spelling of ['--foo','--f']) for(const short of [[spelling,'001'],[spelling+'=001']])
    for(const args of [short,[...short,'--foobar=1e-3'],['--foobar','1e-3',...short]]) {
      const rows=parameterRows(args,[foo,bar]);
      assert.equal(controls(rows).length,2);
      assert.deepEqual(rowArguments(rows),args);
    }
});

test('exact shorter options cannot satisfy required longer options, including row projections',()=>{
  const required={...interval,required:true};
  const rows=parameterRows(['--volume'],[volume,required]);
  assert.match(parameterError(rows,[volume,required]),/--volume-interval is required/);
  const id=rows.find(r=>r.parameter?.name===required.name).id;
  assert.deepEqual(missingRequiredRows(rows),[id]);
  assert.match(invalidParameterRows(rows).get(id),/is required/);
});

test('unsupported exact names still own tokens; true abbreviations remain manual and byte-exact',()=>{
  const unsupported={...volume,supported:false,reason:'Unsupported declaration'};
  assert.equal(controls(parameterRows(['--volume'],[unsupported,interval])).length,1);
  for(const args of [['--vol'],['--vol=1'],['--volume-i','001.0']]) {
    const rows=parameterRows(args,[volume,interval]);
    assert.ok(rows[0].manual);
    assert.equal(rows[0].parameter,undefined);
    assert.deepEqual(rowArguments(rows),args);
    assert.deepEqual(rowArguments(parameterRows(rowArguments(rows),[volume,interval],rows)),args);
  }
});

test('repeats, delimiters, empty tokens and disabled drafts retain exact argv',()=>{
  const args=['--volume','--volume','--unknown','','--','--volume-interval=2'];
  let rows=parameterRows(args,[volume,interval]);
  const draft=rows.find(r=>r.parameter?.name===interval.name);
  assert.ok(!draft.enabled);draft.value='001.0';
  rows=parameterRows(rowArguments(rows),[volume,interval],rows);
  assert.deepEqual(rowArguments(rows),args);
  assert.equal(rows.find(r=>r.parameter?.name===interval.name).value,'001.0');
  assert.ok(rows.filter(r=>r.parameter?.name===volume.name).every(r=>r.manual));
});
