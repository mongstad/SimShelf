import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { RunProgress } from './RunProgress.tsx';
import { ProgressSettings } from './ProgressSettings.tsx';
const render = run => renderToStaticMarkup(React.createElement(RunProgress, {run}));
const report = {current: 2, total: 5, stage: '<solve>', source: 'structured', reported_at: '2026-10-17T12:00:00Z'};
test('unknown progress has no fabricated percentage, count or status', () => {
  for (const status of ['running','failed','cancelled','interrupted']) {
    for (const progress of [undefined,{...report,total:null},{...report,current:null}]) {
      const html = render({status,progress});
      assert.match(html,/Progress unavailable/);
      assert.doesNotMatch(html,/<progress|%| steps|Running|Completed|Failed|Interrupted/);
    }
  }
});
test('known progress is minimal, grouped, accessible and does not mutate metadata', () => {
  const progress = {...report,current:3000,total:50000};
  const run = {status:'running',progress};
  const before = JSON.stringify(run);
  const html = render(run);
  assert.match(html,/<strong>Progress<\/strong>/);
  assert.match(html,/6%/);
  assert.match(html,/<progress[^>]+aria-label="Simulation progress"[^>]+value="3000"[^>]+max="50000"/);
  assert.match(html,/3,000.* \/ .*50,000.* steps/);
  assert.match(html,/&lt;solve&gt;/);
  assert.doesNotMatch(html,/Last reported|Interpreted|simulation API|2026|still running|completion|guarantee/);
  assert.equal(JSON.stringify(run),before);
});
test('final statuses retain the same progress without duplicating execution status', () => {
  for (const status of ['running','failed','cancelled','interrupted']) {
    const html = render({status,progress:{...report,current:5}});
    assert.match(html,/100%/);
    assert.match(html,/5.* \/ .*5.* steps/);
    assert.doesNotMatch(html,/running|completed|failed|interrupted/i);
  }
  assert.equal(render({status:'failed',progress:report}),render({status:'interrupted',progress:report}));
});
test('optional stages and errors remain safe; malformed totals and rounding stay conservative', () => {
  for (const total of [0,-1,Infinity,NaN]) {
    const html = render({status:'running',progress:{...report,total}});
    assert.match(html,/Progress unavailable/);
    assert.doesNotMatch(html,/<progress|%| steps/);
  }
  assert.match(render({status:'running',progress:{...report,current:99999,total:100000}}),/99.9%/);
  assert.doesNotMatch(render({status:'running',progress:{...report,stage:null}}),/progress-stage/);
  assert.match(render({status:'running',progress:{...report,total:null}}),/&lt;solve&gt;/);
  const failed = render({status:'failed',progress_error:'disk unavailable'});
  assert.match(failed,/Progress unavailable/);
  assert.match(failed,/role="alert"/);
  assert.doesNotMatch(failed,/Running/);
});

test('console examples follow the explicitly selected adapter', () => {
  const settings = value => renderToStaticMarkup(React.createElement(ProgressSettings, {value,change:()=>{}}));
  assert.doesNotMatch(settings('off'), /Recognized whole-line examples/);
  assert.match(settings('step'), /step 1,000\/50,000 \(2.0%\)/);
  assert.match(settings('step'), /Step 500 of 1000/);
  assert.match(settings('percent'), /Progress: 25%/);
  assert.match(settings('percent'), /50% complete/);
  assert.match(settings('step'), /Reports never stop a run/);
});


test('completed presentation uses stored total without rewriting original telemetry', () => {
  for (const source of ['structured', 'text:stdout', 'text:stderr']) {
    for (const current of [0, 5000, 5463, null]) {
      const run = {status:'completed',exit_code:0,progress_mode:'step',progress:{...report,current,total:5463,source}};
      const before = structuredClone(run);
      const html = render(run);
      assert.match(html, /<strong>Progress<\/strong>/);
      assert.match(html, /<span>100%<\/span>/);
      assert.match(html, /5,463.* \/ .*5,463.* steps/);
      assert.match(html, /aria-label="Successful process completion"/);
      assert.match(html, /100% process completion; 5,463 of 5,463 steps displayed from the stored total, not a measured progress report/);
      assert.match(html, /value="100" max="100"/);
      assert.doesNotMatch(html, /Last reported|Process completed successfully|91.5%|5,000/);
      assert.deepEqual(run,before);
    }
  }
});

test('100 percent and unsuccessful or active lifecycle states never gain the partial-completion message', () => {
  for (const status of ['running','failed','cancelled','interrupted']) {
    const progress = {...report,current:5};
    const run = {status,progress};
    const before = JSON.stringify(run);
    const html = render(run);
    assert.match(html, /<strong>Progress<\/strong>/);
    assert.match(html, /100%/);
    assert.match(html, /value="5" max="5"/);
    assert.doesNotMatch(html, /Last reported|Process completed successfully/);
    assert.equal(JSON.stringify(run), before);
  }
  // Portal stop/cancellation is recorded as interrupted, never completed.
  for (const status of ['running','failed','cancelled','interrupted']) {
    const html = render({status,progress:{...report,current:4000,total:4123}});
    assert.match(html,/97%/);
    assert.match(html,/value="4000" max="4123"/);
    assert.doesNotMatch(html,/Last reported|Process completed successfully/);
  }
});


test('completed without a valid total shows completion without fabricated counts', () => {
  for (const progress of [undefined, {stage:'Final phase'}, ...[null,0,-1,NaN,Infinity,'5463'].map(total=>({...report,total}))]) {
    const run = {status:'completed',progress};
    const before = structuredClone(run);
    const html = render(run);
    assert.match(html,/<strong>Progress<\/strong>/);
    assert.match(html,/<span>100%<\/span>/);
    assert.match(html,/value="100" max="100"/);
    assert.match(html,/100% process completion; not a measured progress report/);
    assert.doesNotMatch(html,/ steps|Last reported|Progress unavailable|Process completed successfully/);
    if (progress?.stage) assert.match(html,/progress-stage/);
    assert.deepEqual(run,before);
  }
});

test('all non-completed states retain the exact reviewed example and unknown totals', () => {
  for (const status of ['running','failed','cancelled','interrupted']) {
    const run = {status,progress:{...report,current:5000,total:5463}};
    const before = structuredClone(run);
    const html = render(run);
    assert.match(html,/<span>91.5%<\/span>/);
    assert.match(html,/5,000.* \/ .*5,463.* steps/);
    assert.match(html,/value="5000" max="5463"/);
    assert.doesNotMatch(html,/Successful process completion|100%|Last reported/);
    assert.deepEqual(run,before);
    for (const total of [null,0,-1,Infinity,NaN]) {
      const unknown = render({status,progress:{...report,total}});
      assert.match(unknown,/Progress unavailable/);
      assert.doesNotMatch(unknown,/<progress|%| steps/);
    }
  }
});

test('completed accessible and visible display counts share fractional precision', () => {
  const html = render({status:'completed',progress:{...report,current:1,total:2.34567}});
  assert.match(html,/2.34567 of 2.34567 units displayed from the stored total/);
  assert.match(html,/2.34567.* \/ .*2.34567.* units/);
});

test('percentage adapters show precise percentages without fictional step counters', () => {
  for (const source of ['text:stdout', 'text:stderr']) {
    for (const current of [0, 0.002, 0.2, 25.5, 99.99, 100]) {
      for (const status of ['running', 'failed', 'interrupted', 'cancelled', 'completed']) {
        const run = {status, progress_mode:'percent', progress:{...report,source,current,total:100}};
        const before = structuredClone(run);
        const html = render(run);
        assert.match(html, new RegExp(`<span>${status === 'completed' ? 100 : current}%</span>`));
        assert.doesNotMatch(html, /steps|units| \/ /);
        assert.match(html, status === 'completed' ? /not a measured progress report/ : /% reported progress/);
        assert.deepEqual(run,before);
      }
    }
  }
});

test('frozen source mode distinguishes counts from percentages without total heuristics', () => {
  for (const source of ['text:stdout','text:stderr']) {
    const html = render({status:'running',progress_mode:'step',progress:{...report,source,current:8,total:8000}});
    assert.match(html,/8 \/ 8,000 steps/);
    assert.match(html,/8 of 8,000 steps/);
    const hundred = render({status:'running',progress_mode:'step',progress:{...report,source,current:8,total:100}});
    assert.match(hundred,/8 \/ 100 steps/);
    const legacy = render({status:'running',progress:{...report,source,current:8,total:100}});
    assert.match(legacy,/8 \/ 100 units/);
    assert.doesNotMatch(legacy,/steps/);
  }
  const structured = render({status:'running',progress_mode:'percent',progress:report});
  assert.match(structured,/2 \/ 5 steps/);
});

test('fractional work retains numeric precision and neutral units across lifecycle states', () => {
  for (const source of ['structured','text:stdout','text:stderr']) {
    for (const status of ['running','failed','interrupted','completed']) {
      const run = {status,progress_mode:'step',progress:{...report,source,current:0.123456789012345,total:2}};
      const before = structuredClone(run);
      const html = render(run);
      assert.doesNotMatch(html,/steps/);
      assert.match(html,status === 'completed' ? /2 \/ 2 units/ : /0.123456789012345 \/ 2 units/);
      assert.match(html,status === 'completed' ? /not a measured progress report/ : /0.123456789012345 of 2 units/);
      assert.deepEqual(run,before);
    }
  }
});

test('unknown totals stay unavailable across source modes without inventing units', () => {
  for (const source of ['structured','text:stdout','text:stderr']) {
    for (const progress_mode of ['off','step','percent',undefined]) {
      const html = render({status:'interrupted',progress_mode,progress:{...report,source,total:null}});
      assert.match(html,/Progress unavailable/);
      assert.doesNotMatch(html,/<progress|%|steps|units/);
    }
  }
});
