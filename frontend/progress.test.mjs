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


test('successful completion below total identifies actual last report without inventing completion telemetry', () => {
  for (const source of ['structured', 'text:stdout', 'text:stderr']) {
    const run = {status:'completed',exit_code:0,progress:{...report,current:4000,total:4123,source}};
    const before = JSON.stringify(run);
    const html = render(run);
    assert.match(html, /<strong>Last reported progress<\/strong>/);
    assert.match(html, /97%/);
    assert.match(html, /4,000.* \/ .*4,123.* steps/);
    assert.match(html, /aria-label="Successful process completion"/);
    assert.match(html, /aria-valuetext="Process completed; last reported progress 97%, 4,000 of 4,123 steps"/);
    assert.match(html, /value="100" max="100"/);
    assert.doesNotMatch(html, /Process completed successfully\.|100%/);
    assert.equal(JSON.stringify(run), before);
  }
  assert.match(render({status:'completed',progress:{...report,current:0}}), /Last reported progress/);
  assert.match(render({status:'completed',progress:{...report,current:99999,total:100000}}), /99.9%/);
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


test('completed visual state is full with any or no telemetry, without mutating records', () => {
  for (const progress of [undefined, {...report,total:null}, {...report,total:0}, {...report,total:NaN}, {stage:'Final phase'}, {...report,current:0}, {...report,current:5}]) {
    const run = {status:'completed',exit_code:0,progress};
    const before = structuredClone(run);
    const html = render(run);
    assert.match(html,/aria-label="Successful process completion"/);
    assert.match(html,/value="100" max="100"/);
    assert.doesNotMatch(html,/Process completed successfully\./);
    if (progress?.total === 5) {
      assert.match(html,/<strong>Last reported progress<\/strong>/);
      assert.match(html,new RegExp(`${progress.current === 0 ? 0 : 100}%`));
      assert.match(html,/last reported progress/);
    } else {
      assert.match(html,/Progress unavailable/);
      assert.match(html,/no reported progress available/);
      assert.doesNotMatch(html,/%| steps|Last reported progress/);
    }
    if (progress?.stage) assert.match(html,/progress-stage/);
    assert.deepEqual(run,before);
  }
});

test('completed accessible telemetry uses the same fractional precision as visible counts', () => {
  const html = render({status:'completed',progress:{...report,current:1.23456,total:2}});
  assert.match(html,/last reported progress 61.7%, 1.23456 of 2 steps/);
  assert.match(html,/1.23456.* \/ .*2.* steps/);
});
