import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { OverviewActions } from './OverviewActions.tsx';
const render = props => renderToStaticMarkup(React.createElement(OverviewActions,{add:()=>{},record:()=>{},launch:()=>{},...props}));
test('All simulations offers registration without a launch button, including an empty library', () => {
 for (const hasSimulations of [false,true]) {
  const html=render({hasSimulations});
  assert.match(html,/Add simulation/);
  assert.doesNotMatch(html,/New run|Configure and launch/);
  assert.match(html,/Terminal \/ editor/);
  assert.equal((html.match(/disabled=""/g)||[]).length,hasSimulations ? 0 : 1);
  assert.equal((html.match(/<button/g)||[]).length,2);
 }
});
test('selected available simulation offers configuration and terminal, without header registration', () => {
 const html=render({simulation:{available:true},hasSimulations:true});
 assert.doesNotMatch(html,/Add simulation|disabled=/);
 assert.match(html,/class="primary" title="Configure and launch this simulation"/);
 assert.match(html,/New run…/);
 assert.match(html,/Terminal \/ editor/);
 assert.equal((html.match(/aria-hidden="true"/g)||[]).length,2);
});
test('missing source retains disabled New run and available terminal instructions', () => {
 const html=render({simulation:{available:false},hasSimulations:true});
 assert.doesNotMatch(html,/Add simulation/);
 assert.match(html,/New run…/);
 assert.equal((html.match(/disabled=""/g)||[]).length,1);
});
