import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { DeleteScreenshot, withoutScreenshots } from './DeleteScreenshot.tsx';

test('confirmation identifies exact targets and explains irreversible storage effects', () => {
  const html = renderToStaticMarkup(React.createElement(DeleteScreenshot, {
    image: { id: 'image-id', name: '<image>.png', availability: 'missing' },
    run: { id: 'run-id', name: 'Previous run' }, close() {}, deleted() {},
  }));
  for (const text of ['&lt;image&gt;.png', 'Previous run', 'run-id', 'image-id', 'not just this view', 'Existing backups', 'schema 3', 'already missing', 'Cancel', 'Delete screenshot']) assert.ok(html.includes(text), text);
  assert.match(html, /aria-labelledby="delete-screenshot-title"/);
});

test('deletion removes only selected image and replaces cover without mutating stale response', () => {
  const artifacts = ['selected', 'kept'].map(id => ({ id, policy: 'copy', media_type: 'image/png' }));
  artifacts.push({ id: 'external', policy: 'reference', media_type: 'image/png' });
  const run = { id: 'run', artifacts, cover_id: 'selected', image_count: 2, parameters: { unchanged: true } };
  const next = withoutScreenshots(run, new Set(['selected']));
  assert.deepEqual(next.artifacts.map(a => a.id), ['kept', 'external']);
  assert.equal(next.image_count, 1); assert.equal(next.cover_id, 'kept');
  assert.equal(run.artifacts.length, 3); assert.equal(run.cover_id, 'selected');
  assert.deepEqual(next.parameters, run.parameters);
  const empty = withoutScreenshots(run, new Set(['selected', 'kept']));
  assert.equal(empty.image_count, 0); assert.equal(empty.cover_id, null);
});
