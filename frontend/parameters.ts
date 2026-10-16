import { argumentError } from "./arguments";
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
export function present(args: string[], p: Parameter) {
  return args.some((a) =>
    p.flags.some(
      (f) =>
        a === f ||
        a.startsWith(f + "=") ||
        (f.length === 2 && a.startsWith(f) && a.length > 2),
    ),
  );
}
export function overrideTokens(p: Parameter, value: string): string[] {
  if (!p.supported) throw Error("Use the manual editor for " + p.name);
  if (p.action !== "store") return [p.name];
  if (p.type === "int" && !/^[+-]?\d+$/.test(value))
    throw Error(p.name + " needs an integer.");
  if (p.type === "float" && (!value.trim() || !Number.isFinite(Number(value))))
    throw Error(p.name + " needs a finite number.");
  if (p.choices && !p.choices.some((c) => String(c) === value))
    throw Error(p.name + " needs one of the declared choices.");
  // Equals syntax protects values beginning with '-' and preserves empty/space tokens.
  return [p.name + "=" + value];
}
export function appendOverrides(
  args: string[],
  selected: { parameter: Parameter; value: string }[],
) {
  if (args.includes("--"))
    throw Error(
      "Arguments contain --; use the manual editor to preserve positional ordering.",
    );
  let result = [...args];
  for (const { parameter, value } of selected) {
    if (present(result, parameter))
      throw Error(
        parameter.name + " is already in runtime arguments; edit it below.",
      );
    result.push(...overrideTokens(parameter, value));
  }
  const error = argumentError(result);
  if (error) throw Error(error);
  return result;
}
