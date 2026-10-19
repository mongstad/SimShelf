import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { SimulationSettings } from './SimulationSettings.tsx';
import { RemoveSimulation } from './RemoveSimulation.tsx';

test('settings is a labelled dialog with separate workflow actions and safe dismissal', () => {
 const html=renderToStaticMarkup(React.createElement(SimulationSettings,{close:()=>{},relocate:()=>{},remove:()=>{}}));
 assert.match(html,/aria-labelledby="simulation-settings-title"/);
 assert.match(html,/>Change source location…<\/button>/);
 assert.match(html,/>Remove simulation…<\/button>/);
 assert.match(html,/<button autofocus="">Cancel<\/button>/);
 assert.doesNotMatch(html,/Confirm source location|Type the exact|method="post"/);
});

test('removal remains a separate review with initially disabled confirmation', () => {
 const html=renderToStaticMarkup(React.createElement(RemoveSimulation,{id:'a',close:()=>{},removed:()=>{}}));
 assert.match(html,/Reviewing this simulation/);
 assert.match(html,/<button disabled="">Remove simulation<\/button>/);
 assert.match(html,/>Cancel<\/button>/);
});

test('cogwheel fails closed until current authoritative activity is available', async () => {
 const {settingsDisabled, SimulationSettingsButton} = await import('./SimulationSettings.tsx');
 for (const [simulation,current,blocked] of [
  [{administration_active:true},true,true], [{administration_active:false},true,false],
  [{administration_active:false},false,true], [{},true,true],
  [{administration_active:null},true,true],
 ]) {
  assert.equal(settingsDisabled(simulation,current),blocked);
  const html=renderToStaticMarkup(React.createElement(SimulationSettingsButton,{disabled:blocked,onClick:()=>{}}));
  assert.equal(html.includes('disabled=""'),blocked);
  assert.match(html,/aria-label="Simulation settings"/);
  assert.match(html,/aria-haspopup="dialog"/);
  assert.match(html,/simulation-settings-trigger/);
  if(blocked) assert.doesNotMatch(html,/title=/);
 }
});
