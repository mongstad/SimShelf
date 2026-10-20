import React from "react";
import type { Parameter } from "./parameters";
import { matchesDeclaredDefault } from "./parameterDefault";

export function ParameterHint({ parameter: p, token, value, enabled, id }: {
  parameter: Parameter; token: string; value: string | null; enabled: boolean; id: string;
}) {
  // Integers may arrive as decimal strings to preserve signed-64-bit precision.
  const format = (value: string | number | boolean | null) =>
    p.type === "int" ? String(value) : JSON.stringify(value);
  const aliases = p.flags.filter(option => option !== token);
  const current = p.action === "store" ? value : enabled ? String(p.action === "store_true") : null;
  const metadata: string[] = [];
  if (aliases.length) metadata.push(`Aliases: ${aliases.join(", ")}`);
  if (p.action !== "store") metadata.push(`${p.action === "store_false" ? "Sets false" : "Sets true"} when enabled`);
  if (p.default_known && !matchesDeclaredDefault(p, current)) metadata.push(`Default: ${format(p.default)}`);
  if (p.choices) metadata.push(`Choices: ${p.choices.map(format).join(", ")}`);
  return (
    <small className="parameter-hint" id={id}>
      {p.help && <span className="parameter-help">{p.help}</span>}
      {metadata.length > 0 && <span className="parameter-metadata">{metadata.join(" · ")}</span>}
    </small>
  );
}
