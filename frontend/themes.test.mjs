import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const css = readFileSync(new URL('./style.css', import.meta.url), 'utf8');
const names = ['onyx', 'slate', 'linen'];
const tokens = ['bg','surface','sidebar','text','muted','line','accent','accent-text','soft','hover','amber','red','blue','progress-fill','progress-track'];
const palettes = Object.fromEntries(names.map(name => {
  const block = css.match(new RegExp(`:root\\[data-theme="${name}"\\] \\{([^}]+)\\}`))?.[1];
  assert.ok(block, name);
  return [name, Object.fromEntries(block.trim().split(';').filter(x => x.trim()).map(x => x.trim().split(/:\s*/)))];
}));
const luminance = hex => {
  const rgb = hex.slice(1).match(/../g).map(x => parseInt(x, 16) / 255)
    .map(x => x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4);
  return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
};
const contrast = (a, b) => {
  const values = [luminance(a), luminance(b)].sort((a,b) => b-a);
  return (values[0]+.05)/(values[1]+.05);
};

test('optional themes override only complete color tokens and native color scheme', () => {
  for (const [name, values] of Object.entries(palettes)) {
    assert.deepEqual(Object.keys(values).sort(), ['color-scheme', ...tokens.map(x => `--${x}`)].sort());
    assert.equal(values['color-scheme'], name === 'linen' ? 'light' : 'dark');
    for (const token of tokens) assert.match(values[`--${token}`], /^#[0-9a-f]{6}$/);
    // No component, layout, typography, breakpoint or behavior overrides.
    // Existing archive status overrides are color-only component rules.
    for (const [, selectors, declarations] of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
      if (selectors.includes(`[data-theme="${name}"]`) && !declarations.includes('--bg:')) {
        assert.ok(declarations.trim().split(';').filter(x => x.trim()).every(x => /^\s*color:/.test(x)));
      }
    }
  }
});

test('new palettes retain readable text, semantic colors, focus and progress contrast', () => {
  for (const [name, p] of Object.entries(palettes)) {
    for (const bg of ['bg','surface','sidebar','hover','soft']) {
      for (const fg of ['text','muted','accent','amber','red','blue']) {
        assert.ok(contrast(p[`--${fg}`],p[`--${bg}`]) >= 4.5, `${name}: ${fg}/${bg}`);
      }
    }
    assert.ok(contrast(p['--accent'],p['--accent-text']) >= 4.5, name+' primary label');
    assert.ok(contrast(p['--progress-fill'],p['--progress-track']) >= 3, name+' progress');
    // Focus uses accent on each of these surfaces (tested above at >=4.5).
    assert.notEqual(p['--red'],p['--accent']);
    assert.notEqual(p['--amber'],p['--accent']);
  }
});
