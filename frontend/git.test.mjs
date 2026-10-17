import {test} from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {GitObservation} from './GitHistory.tsx';
const render = value => renderToStaticMarkup(React.createElement(GitObservation,{value}));
test('nullable offline provenance remains explicit and inert',()=>{
  const disabled=render({availability:'disabled'});
  assert.match(disabled,/Git is disconnected/);
  assert.doesNotMatch(disabled,/Recent source history/);
  assert.match(render({availability:'unmapped'}),/not mapped/);
  assert.match(render({availability:'unavailable',reason:'Git <unavailable>'}),/Git &lt;unavailable&gt;/);
});
test('raw-byte changes, detached state and source history are distinct from scientific versions',()=>{
  const view={availability:'available',commit:'abc123',branch:null,dirty:true,simulation_dirty:false,subdirectory:'alpha',history:[{commit:'abc123',timestamp:'1000',subject:'<script>unsafe</script>'}],conflicts:true,incomplete:true};
  const before=structuredClone(view),html=render(view);
  assert.match(html,/Detached HEAD/);assert.match(html,/Local changes/);
  assert.match(html,/No raw-byte changes detected/);assert.match(html,/Unresolved Git conflicts/);
  assert.match(html,/not a clean-checkout guarantee/);assert.match(html,/&lt;script&gt;/);
  assert.match(html,/separate from scientific versions/);assert.deepEqual(view,before);
});
