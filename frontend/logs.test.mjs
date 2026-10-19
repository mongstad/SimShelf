import { test } from "node:test";
import assert from "node:assert/strict";
import { build } from "esbuild";
const result = await build({
  entryPoints: ["frontend/logPresentation.ts"],
  bundle: true,
  platform: "node",
  format: "esm",
  write: false,
});
const { logPreference, readLogPreference, saveLogPreference, followLog } =
  await import(
    `data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString("base64")}`
  );
test("defaults and explicit global false values, independently validated", () => {
  for (const raw of [
    null,
    "{",
    "null",
    "[]",
    '"false"',
    '{"wordWrap":0,"autoScroll":"false"}',
  ])
    assert.deepEqual(logPreference(raw), { wordWrap: true, autoScroll: true });
  assert.deepEqual(logPreference('{"wordWrap":false,"autoScroll":false}'), {
    wordWrap: false,
    autoScroll: false,
  });
  assert.deepEqual(logPreference('{"wordWrap":false}'), {
    wordWrap: false,
    autoScroll: true,
  });
});
test("blocked storage retains changes across viewer remounts", () => {
  globalThis.localStorage = {
    getItem() {
      throw Error("denied");
    },
    setItem() {
      throw Error("denied");
    },
  };
  assert.deepEqual(readLogPreference(), { wordWrap: true, autoScroll: true });
  saveLogPreference({ wordWrap: false, autoScroll: false });
  assert.deepEqual(readLogPreference(), { wordWrap: false, autoScroll: false });
});
class Panel extends EventTarget {
  scrollTop = 400;
  scrollHeight = 920;
  clientHeight = 520;
  clientWidth = 600;
  clientLeft = 0;
  getBoundingClientRect() {
    return { left: 0 };
  }
}
function send(target, name, properties = {}) {
  const event = new Event(name);
  Object.assign(event, properties);
  target.dispatchEvent(event);
}
function fixture() {
  globalThis.window = new EventTarget();
  let resize,
    disconnected = false;
  globalThis.ResizeObserver = class {
    constructor(callback) {
      resize = callback;
    }
    observe() {}
    disconnect() {
      disconnected = true;
    }
  };
  const panel = new Panel();
  let pauses = 0;
  const control = followLog(panel, () => pauses++);
  control.setFollowing(true);
  return {
    panel,
    control,
    resize: () => resize(),
    pauses: () => pauses,
    disconnected: () => disconnected,
  };
}
test("append/resize pin while enabled; horizontal and unprompted scroll do not disable", () => {
  const f = fixture();
  f.panel.scrollHeight = 1200;
  f.control.layout();
  assert.equal(f.panel.scrollTop, 1200);
  f.panel.scrollTop = 350;
  send(f.panel, "scroll");
  assert.equal(f.pauses(), 0);
  send(f.panel, "wheel", { deltaX: 100, deltaY: 0 });
  assert.equal(f.pauses(), 0);
  f.resize();
  assert.equal(f.panel.scrollTop, 1200);
  f.control.setFollowing(false);
  f.panel.scrollTop = 200;
  f.panel.scrollHeight = 1400;
  f.control.layout();
  f.resize();
  assert.equal(f.panel.scrollTop, 200);
  f.control.setFollowing(true);
  assert.equal(f.panel.scrollTop, 1400);
  f.control.dispose();
  assert.equal(f.disconnected(), true);
  send(f.panel, "wheel", { deltaY: -100 });
  assert.equal(f.pauses(), 0);
});
test("upward wheel and keyboard pause immediately, including before next append", () => {
  for (const [name, data] of [
    ["wheel", { deltaY: -1 }],
    ["keydown", { key: "PageUp" }],
    ["keydown", { key: "Home" }],
    ["keydown", { key: " ", shiftKey: true }],
  ]) {
    const f = fixture();
    send(f.panel, name, data);
    assert.equal(f.pauses(), 1);
    f.panel.scrollTop = 300;
    f.panel.scrollHeight += 200;
    f.control.layout();
    assert.equal(f.panel.scrollTop, 300);
    f.control.dispose();
  }
});
test("vertical thumb movement pauses; horizontal drag, changed geometry and downward scroll do not", () => {
  const f = fixture();
  send(f.panel, "pointerdown", { button: 0, clientX: 100, clientY: 510 });
  send(f.panel, "scroll");
  assert.equal(f.pauses(), 0);
  send(f.panel, "pointerdown", { button: 0, clientX: 605, clientY: 100 });
  f.panel.clientHeight = 500;
  f.panel.scrollTop = 300;
  send(f.panel, "scroll");
  assert.equal(f.pauses(), 0);
  f.panel.scrollTop = 350;
  send(f.panel, "scroll");
  assert.equal(f.pauses(), 0);
  f.panel.scrollTop = 0;
  send(f.panel, "scroll");
  assert.equal(f.pauses(), 1);
  f.control.dispose();
});
test("touch upward browsing pauses, empty/top input does not", () => {
  const f = fixture();
  f.panel.scrollTop = 0;
  send(f.panel, "wheel", { deltaY: -1 });
  assert.equal(f.pauses(), 0);
  f.panel.scrollTop = 300;
  send(f.panel, "pointerdown", {
    pointerType: "touch",
    clientY: 100,
    clientX: 100,
  });
  send(f.panel, "pointermove", { pointerType: "touch", clientY: 150 });
  assert.equal(f.pauses(), 1);
  f.control.dispose();
});
