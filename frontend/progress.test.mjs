import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { RunProgress } from './RunProgress.tsx';
import { ProgressSettings } from './ProgressSettings.tsx';
const render = run => renderToStaticMarkup(React.createElement(RunProgress, {run}));
const report = {current: 2, total: 5, stage: '<solve>', source: 'structured', reported_at: '2026-10-17T12:00:00Z'};
test('unknown progress has no fabricated percentage, count or status', () => {
  for (const status of ['running','completed','failed','interrupted']) {
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
  for (const status of ['running','completed','failed','interrupted']) {
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
    assert.match(html, /aria-label="Last reported simulation progress"[^>]+value="4000"[^>]+max="4123"/);
    assert.match(html, /Process completed successfully\./);
    assert.doesNotMatch(html, /100%/);
    assert.equal(JSON.stringify(run), before);
  }
  assert.match(render({status:'completed',progress:{...report,current:0}}), /Last reported progress/);
  assert.match(render({status:'completed',progress:{...report,current:99999,total:100000}}), /99.9%/);
});

test('100 percent and unsuccessful or active lifecycle states never gain the partial-completion message', () => {
  for (const status of ['running','completed','failed','interrupted']) {
    const progress = {...report,current:5};
    const run = {status,progress};
    const before = JSON.stringify(run);
    const html = render(run);
    assert.match(html, /<strong>Progress<\/strong>/);
    assert.match(html, /100%/);
    assert.doesNotMatch(html, /Last reported|Process completed successfully/);
    assert.equal(JSON.stringify(run), before);
  }
  // Portal stop/cancellation is recorded as interrupted, never completed.
  for (const status of ['running','failed','interrupted']) {
    const html = render({status,progress:{...report,current:4000,total:4123}});
    assert.match(html,/97%/);
    assert.doesNotMatch(html,/Last reported|Process completed successfully/);
  }
});
