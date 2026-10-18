import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { SimulationSettings } from './SimulationSettings.tsx';
import { RemoveSimulation } from './RemoveSimulation.tsx';

test('settings is a labelled dialog with separate workflow actions and safe dismissal', () => {
 const html=renderToStaticMarkup(React.createElement(SimulationSettings,{name:'A <source>',close:()=>{},relocate:()=>{},remove:()=>{}}));
 assert.match(html,/aria-labelledby="simulation-settings-title"/);
 assert.match(html,/A &lt;source&gt;/);
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
