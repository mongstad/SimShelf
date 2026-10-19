import { argumentError } from "./arguments";
import { overrideTokens, type Parameter } from "./parameters";
export type Row = {
  id: number;
  token: string;
  value: string | null;
  equals: boolean;
  enabled: boolean;
  parameter?: Parameter;
  manual?: string;
  valueOpen?: boolean;
};
export const parameterGroups = [
  "Parameters requiring values",
  "Boolean flags",
  "Manual / undiscovered arguments",
] as const;
export function rowGroup(row: Row): (typeof parameterGroups)[number] {
  return row.parameter?.supported && !row.manual
    ? row.parameter.action === "store"
      ? parameterGroups[0]
      : parameterGroups[1]
    : parameterGroups[2];
}
// Only direct manual editing treats blank as absent. Parsing saved/pasted argv
// continues to preserve explicit empty strings verbatim.
export function manualValue(value: string): Partial<Row> {
  return { value: value === "" ? null : value, valueOpen: true };
}
const optionName = (token: string) => token.split("=", 1)[0];
function possible(token: string, p: Parameter) {
  const name = optionName(token);
  return p.flags.some(
    (f) =>
      name === f ||
      (f.length === 2 &&
        /^-[A-Za-z]/.test(token) &&
        token.length > 2 &&
        token.slice(1).includes(f[1])) ||
      (name.startsWith("--") && name.length > 2 && f.startsWith(name)),
  );
}
export function rowArguments(rows: Row[]): string[] {
  return rows
    .filter((r) => r.enabled)
    .flatMap((r) =>
      r.equals && r.value !== null
        ? [r.token + "=" + r.value]
        : r.value === null
          ? [r.token]
          : [r.token, r.value],
    );
}
export function parameterRows(
  args: string[],
  parameters: Parameter[],
  drafts: Row[] = [],
): Row[] {
  const rows: Row[] = [];
  let positional = false;
  for (let i = 0; i < args.length; i++) {
    const raw = args[i];
    if (raw === "--") positional = true;
    const matches = positional
      ? []
      : parameters.filter((p) => p.flags.includes(optionName(raw)));
    const p = matches.length === 1 ? matches[0] : undefined;
    const known = p?.supported;
    let token = raw,
      value: string | null = null,
      equals = false;
    if (known && raw.includes("=")) {
      const split = raw.indexOf("=");
      token = raw.slice(0, split);
      value = raw.slice(split + 1);
      equals = true;
    } else if (
      !positional &&
      (!known || p.action === "store") &&
      /^--?[^-=\s][^=\s]*$/.test(raw) &&
      args[i + 1] !== undefined &&
      (!args[i + 1].startsWith("-") || /^-(?:\d|\.\d)/.test(args[i + 1]))
    )
      value = args[++i];
    rows.push({
      id: rows.length,
      token,
      value,
      equals,
      enabled: true,
      parameter: p,
      manual: !known
        ? p?.reason || "Manual argument; original tokens preserved."
        : p.action !== "store" && value !== null
          ? "Flag with a value; remove the value or review the declaration."
          : undefined,
    });
  }
  for (const row of rows) {
    if (
      row.parameter?.supported &&
      rows.filter((r) => r.parameter?.name === row.parameter?.name).length > 1
    )
      row.manual =
        "Repeated option; preserved in order for manual conflict review.";
  }
  const beforeDelimiter = args.slice(
    0,
    args.indexOf("--") < 0 ? args.length : args.indexOf("--"),
  );
  for (const p of parameters.filter((p) => p.supported)) {
    if (beforeDelimiter.some((a) => possible(a, p))) continue;
    const draft = drafts.find(
      (r) =>
        !r.enabled &&
        (r.parameter?.name === p.name || p.flags.includes(r.token)),
    );
    const row = {
      id: rows.length,
      token: draft?.token || p.name,
      value: draft?.value ?? null,
      equals: draft?.equals ?? true,
      enabled: false,
      parameter: p,
    };
    // Optional rows inserted before '--' so explicitly enabling one never turns it into a positional token.
    const delimiter = rows.findIndex((r) => r.token === "--");
    if (delimiter < 0) rows.push(row);
    else rows.splice(delimiter, 0, row);
  }
  // Preserve disabled text even when a declaration disappears, as a manual row.
  for (const draft of drafts.filter(
    (r) =>
      !r.enabled &&
      r.value !== null &&
      !parameters.some(
        (p) =>
          p.supported &&
          (p.name === r.parameter?.name || p.flags.includes(r.token)),
      ),
  ))
    rows.push({
      ...draft,
      parameter: undefined,
      manual:
        "Declaration changed or removed; review this preserved manual value.",
    });
  return rows.map((r, id) => ({
    ...r,
    id,
    valueOpen:
      r.valueOpen ??
      drafts.find(
        (d) =>
          d.enabled === r.enabled &&
          d.token === r.token &&
          d.value === r.value &&
          d.equals === r.equals,
      )?.valueOpen,
  }));
}
export function parameterError(rows: Row[], parameters: Parameter[]): string {
  const args = rowArguments(rows),
    limit = argumentError(args);
  if (limit) return limit;
  const normalized = parameterRows(args, parameters);
  for (const p of parameters.filter((p) => p.supported)) {
    const matches = normalized.filter(
      (r) => r.enabled && r.parameter?.name === p.name,
    );
    const before = args.slice(
      0,
      args.indexOf("--") < 0 ? args.length : args.indexOf("--"),
    );
    const uncertain = before.some(
      (a) => possible(a, p) && !p.flags.includes(optionName(a)),
    );
    if (
      p.action === "store" &&
      new Set(
        matches.map((r) =>
          r.value === null || p.type === "str" ? r.value : Number(r.value),
        ),
      ).size > 1
    )
      return `${p.name} occurs more than once with conflicting values. Keep one value or review the declaration.`;
    if (p.required && !matches.length && !uncertain)
      return `${p.name} is required. Enter a value or enable the flag.`;
    for (const r of matches) {
      if (p.action === "store" && r.value === null)
        return `${p.name} needs a value; its displayed default is not passed.`;
      if (p.action !== "store" && r.value !== null)
        return `${p.name} is a flag and does not accept a value.`;
      try {
        overrideTokens(p, r.value ?? "");
      } catch (e) {
        return (e as Error).message;
      }
    }
  }
  return "";
}
