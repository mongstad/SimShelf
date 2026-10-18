// Run with: node --test frontend/sidebar.test.mjs (no browser or test output in checkout).
import { test } from "node:test";
import assert from "node:assert/strict";
import { build } from "esbuild";
const result = await build({
  entryPoints: ["frontend/useSidebar.tsx"],
  bundle: true,
  platform: "node",
  format: "esm",
  write: false,
});
const { sidebarPreference, sidebarMaximum } = await import(
  `data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString("base64")}`
);

test("unusable saved preferences leave navigation expanded at a comfortable width", () => {
  for (const raw of [
    null,
    "",
    "{",
    "null",
    "[]",
    '"480"',
    '{"width":"480","collapsed":"false"}',
    '{"width":1e400}',
  ]) {
    assert.deepEqual(sidebarPreference(raw), { width: 228, collapsed: false });
  }
});
test("saved width is bounded, while collapsed state retains the expanded preference", () => {
  assert.deepEqual(sidebarPreference('{"width":-100,"collapsed":true}'), {
    width: 200,
    collapsed: true,
  });
  assert.deepEqual(sidebarPreference('{"width":100000,"collapsed":true}'), {
    width: 480,
    collapsed: true,
  });
  assert.deepEqual(sidebarPreference('{"width":367.6,"collapsed":true}'), {
    width: 368,
    collapsed: true,
  });
});
test("viewport constraints preserve the preference for a later wider window", () => {
  const saved = sidebarPreference('{"width":460,"collapsed":false}');
  assert.equal(Math.min(saved.width, sidebarMaximum(800)), 320);
  assert.equal(Math.min(saved.width, sidebarMaximum(651)), 200);
  assert.equal(Math.min(saved.width, sidebarMaximum(1280)), 460);
  assert.equal(sidebarMaximum(1920), 480);
});
