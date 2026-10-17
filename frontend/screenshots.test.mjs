import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { DeleteScreenshot, ScreenshotDeletionCopy, withoutScreenshots } from './DeleteScreenshot.tsx';

const copy = schemaVersion => renderToStaticMarkup(React.createElement(ScreenshotDeletionCopy, {
  imageName: '<asset>.png', runName: 'Run Oct 17 · 07:36:36', schemaVersion, missing: false,
}));

test('concise confirmation uses escaped names and keeps target IDs internal', () => {
  const html = renderToStaticMarkup(React.createElement(DeleteScreenshot, {
    image: { id: 'secret-image-id', name: '<asset>.png', availability: 'available' },
    run: { id: 'secret-run-id', name: 'Run Oct 17 · 07:36:36' }, close() {}, deleted() {},
  }));
  for (const text of ['&lt;asset&gt;.png', 'Run Oct 17 · 07:36:36', 'permanently removed from SimShelf', 'cannot be undone', 'Existing backups remain unchanged', 'Cancel', 'Delete screenshot']) assert.ok(html.includes(text), text);
  for (const text of ['secret-image-id', 'secret-run-id', 'blob', 'tombstone', 'audit', 'schema 3']) assert.ok(!html.includes(text), text);
  assert.match(html, /aria-labelledby="delete-screenshot-title"/);
  assert.match(html, /class="screenshot-delete-button" disabled=""/);
  assert.match(html, /aria-hidden="true" focusable="false"/);
});

test('only schema 1 and 2 show the compatibility warning', () => {
  for (const schema of [1, 2]) assert.match(copy(schema), /Older SimShelf versions will no longer open it/);
  for (const schema of [3, null]) assert.doesNotMatch(copy(schema), /Older SimShelf versions|updates this library/);
});

test('missing images retain a short understandable explanation', () => {
  const html = renderToStaticMarkup(React.createElement(ScreenshotDeletionCopy, {
    imageName: 'missing.png', runName: 'Past run', schemaVersion: 3, missing: true,
  }));
  assert.match(html, /already missing/);
  assert.match(html, /removed from this run’s gallery/);
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
