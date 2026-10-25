import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { RecordedVersionEvidence } from './SourceComparison.tsx';
const render = run => renderToStaticMarkup(React.createElement(RecordedVersionEvidence, {run}));
test('recorded version explanation uses captured evidence, including historical mismatches', () => {
  assert.equal(render({version:'legacy'}), '');
  const parameter_metadata = {provenance:{simulation_version:'B',binding_status:'listed bytes verified',binding_reasons:[]}};
  assert.match(render({version:'B',parameter_metadata}), /Version from captured swss.toml/);
  const historical = render({version:'A',parameter_metadata});
  assert.match(historical, /Captured SWSS declaration version/);
  assert.match(historical, /recorded version is retained/);
  assert.doesNotMatch(historical, /Version from captured/);
});
test('stale bindings have actionable reasons; absent metadata is not invented as a version error', () => {
  const html = render({version:'unversioned',parameter_metadata:{provenance:{simulation_version:'B',binding_reasons:['Source binding changed: helper.py']}}});
  assert.match(html, /Why this run is unversioned/);
  assert.match(html, /Source binding changed: helper.py/);
  assert.match(html, /Review root swss.toml and its source hashes/);
  const absent = render({version:'unversioned',parameter_metadata:{warnings:['No companion available']}});
  assert.match(absent, /Recorded metadata diagnostics/);
  assert.doesNotMatch(absent, /Why this run is unversioned|Review root swss.toml/);
});
