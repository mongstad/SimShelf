import { test } from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { RelocateSimulation, RelocationReview } from './RelocateSimulation.tsx';

test('preview names both paths and discloses history, references and consent boundaries', () => {
 const review={old_path:'/old/<source>',new_path:'/new/source',warnings:['Missing interpreter <check>']};
 const html=renderToStaticMarkup(React.createElement(RelocationReview,{review}));
 assert.match(html,/Previous source folder/);assert.match(html,/New source folder/);
 assert.match(html,/\/old\/&lt;source&gt;/);assert.match(html,/\/new\/source/);
 assert.match(html,/does not move or delete files/);
 assert.match(html,/reference-only files.*original locations/);
 assert.match(html,/automatic archival consent will be cleared/);
 assert.match(html,/master archive connection stays unchanged/);
 assert.match(html,/Missing interpreter &lt;check&gt;/);
});

test('path entry is labelled and initial action cannot confirm an unreviewed target', () => {
 const simulation={id:'stable',name:'Existing',root:'/missing/root'};
 const html=renderToStaticMarkup(React.createElement(RelocateSimulation,{simulation,close:()=>{},relocated:()=>{}}));
 assert.match(html,/aria-labelledby="relocate-title"/);
 assert.match(html,/New source folder<input/);
 assert.match(html,/Existing simulation ID/);
 assert.match(html,/Review new location/);
 assert.doesNotMatch(html,/Confirm source location/);
 assert.match(html,/disabled=""/);
});
