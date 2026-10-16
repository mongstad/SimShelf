export type Parameter = {
  flags: string[];
  name: string;
  help: string;
  type: string;
  action: string;
  choices: (string | number | boolean)[] | null;
  default_known: boolean;
  default: string | number | boolean | null;
  required: boolean;
  source: string;
  supported: boolean;
  reason: string;
};
export type Discovery = {
  parameters: Parameter[];
  warnings: string[];
  source: string;
  fingerprint: string | null;
};
export function overrideTokens(p: Parameter, value: string): string[] {
  if (!p.supported) throw Error("Use the manual editor for " + p.name);
  if (p.action !== "store") return [p.name];
  if (p.type === "int" && !/^[+-]?\d+$/.test(value))
    throw Error(p.name + " needs an integer.");
  if (
    p.type === "float" &&
    (!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(value) ||
      !Number.isFinite(Number(value)))
  )
    throw Error(p.name + " needs a finite number.");
  if (
    p.choices &&
    !p.choices.some((c) =>
      p.type === "str"
        ? typeof c === "string" && c === value
        : typeof c === "number" && c === Number(value),
    )
  )
    throw Error(p.name + " needs one of the declared choices.");
  // Equals syntax protects values beginning with '-' and preserves empty/space tokens.
  return [p.name + "=" + value];
}
