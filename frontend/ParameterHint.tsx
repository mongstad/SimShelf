import React from "react";
import type { Parameter } from "./parameters";

export function ParameterHint({ parameter: p, token, id }: {
  parameter: Parameter; token: string; id: string;
}) {
  // Integers may arrive as decimal strings to preserve signed-64-bit precision.
  const format = (value: string | number | boolean | null) =>
    p.type === "int" ? String(value) : JSON.stringify(value);
  const aliases = p.flags.filter(option => option !== token);
  return (
    <small className="parameter-hint" id={id}>
      {p.help && <span className="parameter-help">{p.help}</span>}
      <span className="parameter-metadata">
        {aliases.length > 0 && <>Aliases: {aliases.join(", ")} · </>}
        {p.action !== "store" && <>{p.action === "store_false" ? "Sets false" : "Sets true"} when enabled · </>}
        {p.default_known ? <>Declared default (hint): {format(p.default)}</> : "Declared default: unknown"}
        {p.choices && <> · Choices: {p.choices.map(format).join(", ")}</>}
      </span>
    </small>
  );
}
