import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { SourceBadge } from './EntrypointWarning';
const render = run => renderToStaticMarkup(React.createElement(SourceBadge, {run}));
test('whole-snapshot changes and missing historical projection cannot trigger the named warning', () => {
  for (const source_change of ['changed','text-only','same','baseline']) {
    assert.doesNotMatch(render({source_change}), /Captured source changed within version/);
    assert.doesNotMatch(render({source_change,entrypoint_warning:{warn:false,status:'same'}}), /Captured source changed within version/);
  }
});
test('primary byte edits including comments use the explicit warning projection', () => {
  for (const source_change of ['changed','text-only'])
    assert.match(render({source_change,entrypoint_warning:{warn:true,status:'changed'}}), /Captured source changed within version/);
});
test('version changes and unavailable evidence suppress the warning', () => {
  for (const status of ['version-changed','unavailable'])
    assert.equal(render({source_change:'changed',entrypoint_warning:{warn:false,status}}), '');
});
