import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { chronological, runSequence, neighbors, RunNavigation } from './RunNavigation.tsx';
const run = (id, simulation_id='A', started_at='2026-01-01T00:00:00Z') => ({id,simulation_id,started_at});
test('snapshot retains visible filtered order, isolates simulation and deduplicates IDs', () => {
 const list=[run('3'),run('b','B'),run('1'),run('3')];
 const sequence=runSequence(list,'A');
 assert.deepEqual(sequence.ids,['3','1']);
 list.unshift(run('new'));
 assert.deepEqual(sequence.ids,['3','1']);
 assert.deepEqual(neighbors(sequence,'3'),{previous:undefined,next:'1'});
 assert.deepEqual(neighbors(sequence,'1'),{previous:'3',next:undefined});
 assert.deepEqual(neighbors(sequence,'b'),{previous:undefined,next:undefined});
 assert.deepEqual(runSequence(list,'B').ids,['b']);
});
test('chronological fallback is stable under equal timestamps and across year boundaries', () => {
 const list=[run('z'),run('old','A','2025-12-31T23:59:59Z'),run('a')];
 assert.deepEqual(chronological(list).map(r=>r.id),['a','z','old']);
 assert.deepEqual(list.map(r=>r.id),['z','old','a']);
});
test('empty, single, unavailable and removed entries never wrap or cross simulations', () => {
 for(const ids of [[],['only']]) {
  assert.deepEqual(neighbors({simulationId:'A',ids},'only'),{previous:undefined,next:undefined});
 }
 const sequence=runSequence([run('3'),run('2'),run('1')],'A');
 sequence.ids=sequence.ids.filter(id=>id!=='2');
 assert.equal(neighbors(sequence,'3').next,'1');
 assert.deepEqual(neighbors(sequence,'deleted'),{previous:undefined,next:undefined});
});
test('navigation exposes semantic controls, boundary state and order guidance', () => {
 const html=renderToStaticMarkup(React.createElement(RunNavigation,{id:'3',sequence:runSequence([run('3'),run('1')],'A'),navigate:()=>{},close:()=>{}}));
 assert.match(html,/nav[^>]+aria-label="Run navigation"/);
 assert.match(html,/disabled="">← Previous run/);
 assert.match(html,/>Next run →/);
 assert.match(html,/Back to runs/);
 assert.match(html,/Following the opened list, within this simulation/);
 const fallback=renderToStaticMarkup(React.createElement(RunNavigation,{id:'3',sequence:runSequence([run('3')],'A',true),navigate:()=>{},close:()=>{}}));
 assert.match(fallback,/1,000 recent runs/);
});
