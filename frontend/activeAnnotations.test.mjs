import { test } from 'node:test';
import assert from 'node:assert/strict';
import { api, connect } from './api.ts';
import { runRequests } from './runRequests.ts';

const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };

test('API rejects stale instance tokens and reconnect uses the new token without retrying writes', async t => {
  let instance = 'old', writes = 0;
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    if (path === '/api/workspace') return Response.json({ token: instance });
    assert.equal(options.method, 'PATCH');
    writes++;
    if (options.headers['X-SimShelf-Token'] !== instance)
      return Response.json({detail:'Refresh SimShelf before saving.'}, {status:403});
    return Response.json({status:'running',tags:['favorite'],can_stop:false});
  });
  await connect();
  instance = 'new';
  await assert.rejects(api('/runs/active', {method:'PATCH',body:'{"tags":["favorite"]}'}), /Refresh SimShelf before saving/);
  assert.equal(writes, 1);
  await connect();
  const saved = await api('/runs/active', {method:'PATCH',body:'{"tags":["favorite"]}'});
  assert.deepEqual(saved.tags, ['favorite']);
  assert.equal(saved.can_stop, false);
  assert.equal(writes, 2);
});

for (const status of ['running', 'completed']) {
  test(`${status}: late poll cannot replace a confirmed favorite; later fresh poll can`, async () => {
    const gate = runRequests(); gate.activate();
    let confirmed = {status, tags:[]};
    const slow = deferred(), ticket = gate.read();
    const poll = slow.promise.then(data => { if (gate.current(ticket)) confirmed = data; });
    const save = gate.save();
    assert.equal(gate.read(), null);
    if (gate.current(save)) confirmed = {status, tags:['favorite']};
    gate.finish();
    slow.resolve({status, tags:[]});
    await poll;
    assert.deepEqual(confirmed.tags, ['favorite']);
    const fresh = gate.read();
    if (gate.current(fresh)) confirmed = {status, tags:['favorite'], notes:'kept'};
    assert.deepEqual(confirmed.tags, ['favorite']);
    assert.equal(confirmed.notes, 'kept');
  });
}
