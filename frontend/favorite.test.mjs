import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { RunTitle } from './RunTitle.tsx';
import { runRequests } from './runRequests.ts';

test('title is separate from a named, decorative, native pressed-state toggle', () => {
  for (const favorite of [false, true]) {
    const html = renderToStaticMarkup(React.createElement(RunTitle, {
      name: 'Long <scientific> run', favorite, busy: false, toggle() {},
    }));
    assert.match(html, /<h1>Long &lt;scientific&gt; run<\/h1><button/);
    assert.match(html, new RegExp(`aria-pressed="${favorite}"`));
    assert.match(html, new RegExp(`aria-label="${favorite ? 'Unfavorite' : 'Favorite'} run"`));
    assert.match(html, /aria-hidden="true"/);
    assert.match(html, new RegExp(`fill="${favorite ? 'currentColor' : 'none'}"`));
    assert.doesNotMatch(html, /disabled/);
  }
});
test('pending save disables activation while retaining confirmed state', () => {
  const html = renderToStaticMarkup(React.createElement(RunTitle, {
    name: 'Run', favorite: false, busy: true, toggle() {},
  }));
  assert.match(html, /disabled=""/);
  assert.match(html, /aria-pressed="false"/);
});
test('save rejects duplicate submissions and invalidates older polling results/errors', () => {
  const gate = runRequests(); gate.activate();
  const read = gate.read(), save = gate.save();
  assert.equal(gate.current(read), false);
  assert.equal(gate.save(), null);
  assert.equal(gate.read(), null);
  assert.equal(gate.current(save), true);
  gate.finish();
  assert.equal(gate.current(read), false);
  assert.equal(gate.current(gate.read()), true);
});
test('failed save unlocks retry without accepting stale reads', () => {
  const gate = runRequests(); gate.activate();
  const read = gate.read(); gate.save(); gate.finish();
  assert.equal(gate.current(read), false);
  assert.notEqual(gate.save(), null);
});
test('navigation discards old read/save completions and keeps the next run independent', () => {
  const old = runRequests(); old.activate(); const save = old.save(); old.dispose();
  const next = runRequests(); next.activate(); const read = next.read();
  assert.equal(old.current(save), false);
  old.finish();
  assert.equal(next.current(read), true);
  assert.equal(old.read(), null);
});
test('out-of-order reads cannot replace newer run state', () => {
  const gate = runRequests(); gate.activate();
  const first = gate.read(), second = gate.read();
  assert.equal(gate.current(first), false);
  assert.equal(gate.current(second), true);
});
