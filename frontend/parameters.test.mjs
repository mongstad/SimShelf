import { test } from "node:test";
import assert from "node:assert/strict";
import {
  parameterRows,
  rowArguments,
  parameterError,
} from "./parameterRows.ts";
const p = {
  name: "--dt",
  flags: ["--dt", "-d"],
  action: "store",
  type: "float",
  choices: null,
  supported: true,
  required: false,
  default_known: true,
  default: 0.1,
};
const flag = {
  ...p,
  name: "--quiet",
  flags: ["--quiet"],
  action: "store_true",
};
test("discovered rows start disabled; defaults never become argv", () => {
  const rows = parameterRows([], [p, flag]);
  assert.equal(rows.length, 2);
  assert.ok(rows.every((r) => !r.enabled && r.value === null));
  assert.deepEqual(rowArguments(rows), []);
  assert.equal(parameterError(rows, [p, flag]), "");
  rows[0].enabled = true;
  assert.match(parameterError(rows, [p, flag]), /needs a value/);
  rows[0].value = "-.25";
  assert.deepEqual(rowArguments(rows), ["--dt=-.25"]);
  rows[1].enabled = true;
  assert.deepEqual(rowArguments(rows), ["--dt=-.25", "--quiet"]);
  rows[0].enabled = false;
  assert.deepEqual(rowArguments(rows), ["--quiet"]);
});
test("saved equals and separate values display separately without changing tokens or alias", () => {
  for (const args of [
    ["--dt", "-0.25"],
    ["--dt=-0.25"],
    ["-d", "-0.25"],
    ["--dt="],
  ]) {
    const rows = parameterRows(args, [p]);
    assert.equal(rows.length, 1);
    assert.ok(!rows[0].token.includes("="));
    assert.deepEqual(rowArguments(rows), args);
  }
  const rows = parameterRows(["--quiet", "input file"], [flag]);
  assert.equal(rows[0].value, null);
  assert.equal(rows[1].token, "input file");
  assert.deepEqual(rowArguments(rows), ["--quiet", "input file"]);
});
test("unknown/repeated/positional and attached/abbreviated forms remain exact manual fallbacks", () => {
  for (const args of [
    ["--unknown", "a b", "--tag=x", "--tag=y", "input.txt"],
    ["-d.25"],
    ["--d=.25"],
    ["--dt=1", "--dt", "2"],
    ["--", "--dt=1", "input.txt"],
  ]) {
    const rows = parameterRows(args, [p]);
    assert.deepEqual(rowArguments(rows), args);
    if (args[0] !== "--")
      assert.equal(
        rows.filter((r) => !r.enabled && r.parameter?.name === "--dt").length,
        args[0] === "--unknown" ? 1 : 0,
      );
  }
  assert.match(
    parameterError(parameterRows(["--dt=1", "--dt", "2"], [p]), [p]),
    /more than once/,
  );
});
test("rescan preserves disabled edited values and marks removed declarations manual", () => {
  let rows = parameterRows([], [p]);
  rows[0].value = "42";
  rows = parameterRows(rowArguments(rows), [{ ...p, default: 0.2 }], rows);
  assert.equal(rows[0].value, "42");
  assert.equal(rows[0].enabled, false);
  assert.deepEqual(rowArguments(rows), []);
  rows = parameterRows(rowArguments(rows), [], rows);
  assert.equal(rows[0].value, "42");
  assert.match(rows[0].manual, /removed/);
});
test("required values, boolean values, types and choices are validated without guessing positionals", () => {
  const required = { ...p, required: true };
  assert.match(
    parameterError(parameterRows([], [required]), [required]),
    /required/,
  );
  assert.match(
    parameterError(parameterRows(["--dt"], [required]), [required]),
    /needs a value/,
  );
  assert.match(
    parameterError(parameterRows(["--dt=Infinity"], [p]), [p]),
    /finite/,
  );
  assert.match(
    parameterError(parameterRows(["--quiet=yes"], [flag]), [flag]),
    /does not accept/,
  );
  assert.match(
    parameterError(parameterRows(["--dt=3"], [{ ...p, choices: [1, 2] }]), [
      { ...p, choices: [1, 2] },
    ]),
    /choices/,
  );
  assert.match(
    parameterError(parameterRows(["--dt=1.5"], [{ ...p, type: "int" }]), [
      { ...p, type: "int" },
    ]),
    /integer/,
  );
  const string = { ...p, type: "str" };
  assert.equal(
    parameterError(parameterRows(["--dt="], [string]), [string]),
    "",
  );
});
test("disabled options before separator enable as options without moving existing tokens", () => {
  const rows = parameterRows(["--", "file"], [p]);
  rows[0].enabled = true;
  rows[0].value = "-.5";
  assert.deepEqual(rowArguments(rows), ["--dt=-.5", "--", "file"]);
});

test("removed and restored declarations recover one disabled row without losing its draft", () => {
  let rows = parameterRows([], [p]);
  rows[0].value = "42";
  rows = parameterRows(rowArguments(rows), [], rows);
  rows = parameterRows(rowArguments(rows), [p], rows);
  assert.equal(rows.length, 1);
  assert.equal(rows[0].value, "42");
  assert.equal(rows[0].enabled, false);
  assert.deepEqual(rowArguments(rows), []);
});
test("ambiguous clusters stay manual and numeric choices compare converted values", () => {
  const rows = parameterRows(["-xd.25"], [p]);
  assert.equal(rows.length, 1);
  assert.deepEqual(rowArguments(rows), ["-xd.25"]);
  assert.match(
    parameterError(parameterRows(["--dt=0x10"], [p]), [p]),
    /finite/,
  );
  const choice = { ...p, choices: [1] };
  assert.equal(
    parameterError(parameterRows(["--dt=1.0"], [choice]), [choice]),
    "",
  );
  assert.deepEqual(rowArguments(parameterRows(["--dt", "-.25"], [p])), [
    "--dt",
    "-.25",
  ]);
});

test("disabled edits survive a declaration becoming unsupported", () => {
  let rows = parameterRows([], [p]);
  rows[0].value = "42";
  rows = parameterRows(
    [],
    [{ ...p, supported: false, reason: "Custom action" }],
    rows,
  );
  assert.equal(rows.length, 1);
  assert.equal(rows[0].value, "42");
  assert.equal(rows[0].enabled, false);
  assert.match(rows[0].manual, /changed/);
  assert.deepEqual(rowArguments(rows), []);
  rows = parameterRows([], [p], rows);
  assert.equal(rows.length, 1);
  assert.equal(rows[0].value, "42");
});

test("repeated boolean flags and identical scalar values remain valid manual rows", () => {
  const args = ["--quiet", "--quiet", "--dt=1", "--dt", "1.0"];
  const rows = parameterRows(args, [p, flag]);
  assert.deepEqual(rowArguments(rows), args);
  assert.equal(parameterError(rows, [p, flag]), "");
  assert.ok(rows.every((r) => r.manual));
});

test("grouping changes presentation only, preserving mixed order, aliases and syntax", async () => {
  const { rowGroup, parameterGroups } = await import("./parameterRows.ts");
  const args = [
    "input.txt",
    "--quiet",
    "-d",
    "0.25",
    "--other",
    "",
    "--dt=0.25",
    "--",
    "--quiet",
  ];
  const rows = parameterRows(args, [p, flag]);
  const grouped = parameterGroups.map((group) =>
    rows.filter((r) => rowGroup(r) === group),
  );
  assert.equal(grouped.flat().length, rows.length);
  assert.deepEqual(rowArguments(rows), args);
  assert.deepEqual(
    rowArguments(parameterRows(rowArguments(rows), [flag, p], rows)),
    args,
  );
  assert.ok(
    rows
      .filter((r) => r.parameter?.name === "--dt")
      .every((r) => rowGroup(r) === parameterGroups[2]),
  );
});
test("manual blank edits omit values, explicit empties and saved/pasted empties stay exact", async () => {
  const { manualValue } = await import("./parameterRows.ts");
  let row = {
    id: 0,
    token: "--something",
    value: null,
    enabled: true,
    equals: false,
    manual: "Manual",
  };
  row = { ...row, ...manualValue("") };
  assert.deepEqual(rowArguments([row]), ["--something"]);
  assert.equal(parameterError([row], []), "");
  row = { ...row, ...manualValue("192") };
  assert.deepEqual(rowArguments([row]), ["--something", "192"]);
  row = { ...row, value: "" };
  assert.deepEqual(rowArguments([row]), ["--something", ""]);
  for (const args of [["--something", ""], ["--something="], [""]])
    assert.deepEqual(rowArguments(parameterRows(args, [])), args);
  row = { ...row, ...manualValue("") };
  assert.deepEqual(rowArguments([row]), ["--something"]);
  const rescanned = parameterRows(rowArguments([row]), [], [row]);
  assert.equal(rescanned[0].valueOpen, true);
});
test("fixture flags emit tokens only and required discovered values remain validated", async () => {
  const { rowGroup, parameterGroups, manualValue } =
    await import("./parameterRows.ts");
  const wave = { ...flag, name: "--wavez", flags: ["--wavez"] };
  const plots = {
    ...flag,
    name: "--no-plots",
    flags: ["--no-plots"],
    action: "store_false",
  };
  const n = { ...p, name: "--N", flags: ["--N"], type: "int" };
  const precision = {
    ...p,
    name: "--precision",
    flags: ["--precision"],
    type: "str",
    choices: ["single", "double"],
  };
  const args = ["--wavez", "--N", "192", "--no-plots", "--precision=double"];
  const rows = parameterRows(args, [wave, n, plots, precision]);
  assert.deepEqual(rowArguments(rows), args);
  assert.equal(parameterError(rows, [wave, n, plots, precision]), "");
  assert.equal(
    rows.filter((r) => rowGroup(r) === parameterGroups[1]).length,
    2,
  );
  assert.equal(
    rows.filter((r) => rowGroup(r) === parameterGroups[0]).length,
    2,
  );
  const manual = {
    id: 0,
    token: "--dt",
    enabled: true,
    equals: false,
    ...manualValue(""),
  };
  assert.deepEqual(rowArguments([manual]), ["--dt"]);
  assert.equal(parameterError([manual], []), "");
  assert.match(parameterError([manual], [p]), /needs a value/);
});

test('SWSS exact argv survives rescan including aliases empties repeats and delimiter', () => {
  const number = {...p, name:'--N', flags:['--N','-n'], type:'int'};
  const label = {...p, name:'--label', flags:['--label'], type:'str'};
  const args = ['--N','00192','--dt=1e-3','--label','','-n','+192','--unknown','--','--quiet'];
  const rows = parameterRows(args, [number,p,label,flag]);
  assert.deepEqual(rowArguments(rows), args);
  assert.deepEqual(rowArguments(parameterRows(rowArguments(rows), [number,p,label,flag], rows)), args);
  assert.ok(rows.filter(r=>r.parameter?.name==='--N').every(r=>r.manual));
  assert.equal(rows.at(-1).parameter, undefined);
});
test('SWSS short new options use separate tokens and int64 limits preserve spelling', () => {
  const n = {...p,name:'-n',flags:['-n'],type:'int'};
  const rows = parameterRows([], [n]); rows[0].enabled=true; rows[0].value='00192';
  assert.deepEqual(rowArguments(rows), ['-n','00192']);
  rows[0].value='9223372036854775808'; assert.match(parameterError(rows,[n]),/integer/);
  rows[0].value='-9223372036854775808'; assert.equal(parameterError(rows,[n]),'');
});

test('short attached equals values remain manual and byte-identical', () => {
  const rows=parameterRows(['-d=1e-3'],[p]);
  assert.deepEqual(rowArguments(rows),['-d=1e-3']);
  assert.ok(rows[0].manual);
});
test('signed-64-bit choices compare exact integers without JSON precision loss', () => {
 const n={...p,type:'int',choices:['9223372036854775807']};
 const rows=parameterRows(['--dt=+09223372036854775807'],[n]);
 assert.equal(parameterError(rows,[n]),'');
 assert.deepEqual(rowArguments(rows),['--dt=+09223372036854775807']);
 rows[0].value='9223372036854775806';assert.match(parameterError(rows,[n]),/choices/);
});

test("required omission projection preserves argv and ignores optional defaults/manual ambiguity", async () => {
  const { missingRequiredRows } = await import('./parameterRows.ts');
  const required = { ...p, required: true };
  const requiredFlag = { ...flag, required: true };
  const label = { ...required, name: '--label', flags: ['--label'], type: 'str' };
  const optionalUnknown = { ...p, name: '--unknown', flags: ['--unknown'], default_known: false };
  const declarations = [required, requiredFlag, label, optionalUnknown];
  const rows = parameterRows([], declarations);
  assert.deepEqual(missingRequiredRows(rows), [0, 1, 2]);
  assert.deepEqual(rowArguments(rows), []);
  for (const args of [ ['-d','1e-3','--quiet','--label='], ['--dt=001','--quiet','--label',''] ]) {
    const supplied = parameterRows(args, declarations);
    assert.deepEqual(missingRequiredRows(supplied), []);
    assert.deepEqual(rowArguments(supplied), args);
  }
  const noValue = parameterRows(['--dt'], [required]);
  assert.deepEqual(missingRequiredRows(noValue), [0]);
  assert.deepEqual(rowArguments(noValue), ['--dt']);
  const afterDelimiter = parameterRows(['--','--quiet'], [requiredFlag]);
  assert.equal(missingRequiredRows(afterDelimiter).length, 1);
  assert.deepEqual(rowArguments(afterDelimiter), ['--','--quiet']);
  assert.deepEqual(missingRequiredRows(parameterRows(['--dt','1','--dt','2'], [required])), []);
  assert.deepEqual(missingRequiredRows(parameterRows(['--d=1'], [required])), []);
  assert.deepEqual(missingRequiredRows(parameterRows([], [])), []);
});

test('typed error projection includes supplied invalid values without changing exact argv', async () => {
  const {invalidParameterRows} = await import('./parameterRows.ts');
  for (const args of [['--dt='], ['-d', 'NaN'], ['--dt=Infinity'], []]) {
    const rows = parameterRows(args, [{...p, required:true}]);
    const errors = invalidParameterRows(rows);
    assert.equal(errors.size, 1);
    assert.equal(errors.get(rows[0].id), parameterError(rows, [{...p,required:true}]));
    assert.deepEqual(rowArguments(rows), args);
  }
});
test('typed errors respect disabled drafts, choices and manual ambiguity', async () => {
  const {invalidParameterRows} = await import('./parameterRows.ts');
  const rows = parameterRows([], [p]); rows[0].value = 'invalid draft';
  assert.equal(invalidParameterRows(rows).size, 0);
  const choice = {...p, choices:[1,2]};
  assert.equal(invalidParameterRows(parameterRows(['--dt=3'],[choice])).size, 1);
  for (const args of [['--dt=1','--dt=2'],['-d.25'],['--','--dt=']]) {
    const manual = parameterRows(args,[p]);
    assert.equal(invalidParameterRows(manual).size, 0);
    assert.deepEqual(rowArguments(manual), args);
  }
});
