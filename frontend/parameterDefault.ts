import type { Parameter } from "./parameters";

// Compare decimal spellings without Number rounding or expanding exponents.
function decimal(value: string): string | null {
  const match = /^([+-]?)(\d+(?:\.\d*)?|\.\d+)(?:[eE]([+-]?\d+))?$/.exec(value);
  if (!match) return null;
  const fraction = match[2].split(".")[1]?.length || 0;
  let digits = match[2].replace(".", "").replace(/^0+/, "");
  if (!digits) return "0";
  const trailing = digits.length - digits.replace(/0+$/, "").length;
  digits = digits.slice(0, digits.length - trailing);
  return `${match[1] === "-" ? "-" : ""}${digits}e${BigInt(match[3] || "0") - BigInt(fraction) + BigInt(trailing)}`;
}

export function matchesDeclaredDefault(p: Parameter, value: string | null): boolean {
  if (!p.default_known || value === null) return false;
  if (p.type === "str") return value === p.default;
  if (p.type === "int") {
    return /^[+-]?\d+$/.test(value) && /^[+-]?\d+$/.test(String(p.default)) &&
      BigInt(value) === BigInt(String(p.default));
  }
  if (p.type === "float") {
    const current = decimal(value), declared = decimal(String(p.default));
    return current !== null && declared !== null && current === declared;
  }
  return value === String(p.default);
}
