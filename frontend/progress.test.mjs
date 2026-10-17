import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { RunProgress } from './RunProgress.tsx';
import { ProgressSettings } from './ProgressSettings.tsx';
const render = run => renderToStaticMarkup(React.createElement(RunProgress, {run}));
const report = {current: 2, total: 5, stage: '<solve>', source: 'structured', reported_at: '2026-10-17T12:00:00Z'};
test('unknown progress never fabricates a percentage or progressbar', () => {
  const html = render({status:'running'});
  assert.match(html,/Running · progress not reported/);
  assert.doesNotMatch(html,/<progress|%|ETA/);
  assert.doesNotMatch(render({status:'running',progress:{...report,total:null}}), /<progress|%/);
});
test('known telemetry is accessible, escaped and separate from success', () => {
  const html = render({status:'running',progress:report});
  assert.match(html,/40%/); assert.match(html,/<progress[^>]+value="2"[^>]+max="5"/);
  assert.match(html,/&lt;solve&gt;/); assert.match(html,/still running/);
  assert.match(render({status:'failed',progress:{...report,current:5}}),/Run failed/);
  assert.match(render({status:'interrupted',progress:{...report,source:'text:stderr'}}),/Interpreted from stderr/);
});
test('malformed totals stay unknown and rounding does not imply early 100%', () => {
  for (const total of [0,-1,Infinity,NaN]) assert.doesNotMatch(render({status:'running',progress:{...report,total}}),/<progress/);
  assert.match(render({status:'running',progress:{...report,current:99999,total:100000}}),/99.9%/);
  assert.equal(render({status:'completed'}),'');
  const failed = render({status:'failed',progress_error:'disk unavailable'});
  assert.match(failed,/Progress unavailable/);
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
