/** Display grouping only: the persisted contract remains an ordered string array. */
export type ArgumentRow = { token: string; value: string | null };

export function groupArguments(args: string[]): ArgumentRow[] {
  const rows: ArgumentRow[] = [];
  let positional = false;
  for (let i = 0; i < args.length; i++) {
    const token = args[i];
    if (token === "--") positional = true;
    const next = args[i + 1];
    const paired =
      !positional &&
      /^--?[^-=\s][^=\s]*$/.test(token) &&
      next !== undefined &&
      (!next.startsWith("-") || /^-\d/.test(next));
    rows.push({ token, value: paired ? args[++i] : null });
  }
  return rows;
}

export function flattenArguments(rows: ArgumentRow[]): string[] {
  return rows.flatMap(({ token, value }) =>
    value === null ? [token] : [token, value],
  );
}

export function argumentError(args: string[]): string {
  if (args.length > 256) return "Use at most 256 arguments.";
  if (args.some((arg) => arg.includes("\0")))
    return "Arguments cannot contain NUL characters.";
  if (args.some((arg) => [...arg].length > 8192))
    return "Each argument must be at most 8192 characters.";
  if (args.reduce((sum, arg) => sum + [...arg].length, 0) > 65536)
    return "Arguments must total at most 65536 characters.";
  return "";
}

/** Quote a display command. It is never evaluated or passed to a shell. */
export function formatCommand(args: string[]): string {
  return args
    .map((arg) =>
      /^[a-zA-Z0-9_./:=+-]+$/.test(arg)
        ? arg
        : "'" + arg.replaceAll("'", "'\"'\"'") + "'",
    )
    .join(" ");
}

/** Shell-style quoting only; no expansion, operators, comments, or execution. */
export function parseArguments(text: string): string[] {
  const args: string[] = [];
  let token = "",
    started = false,
    quote = "";
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quote === "'") {
      if (c === "'") quote = "";
      else token += c;
    } else if (c === "\\") {
      if (i + 1 === text.length)
        throw new Error(
          "Trailing backslash: add the escaped character or remove the backslash.",
        );
      const next = text[i + 1];
      if (quote === '"' && !['"', "\\", "$", "`", "\n"].includes(next))
        token += c;
      else {
        i++;
        if (next !== "\n") {
          token += next;
          started = true;
        }
      }
    } else if (quote === '"') {
      if (c === '"') quote = "";
      else token += c;
    } else if (c === "'" || c === '"') {
      quote = c;
      started = true;
    } else if (/\s/.test(c)) {
      if (started) {
        args.push(token);
        token = "";
        started = false;
      }
    } else {
      token += c;
      started = true;
    }
  }
  if (quote)
    throw new Error(`Unclosed ${quote === "'" ? "single" : "double"} quote.`);
  if (started) args.push(token);
  const error = argumentError(args);
  if (error) throw new Error(error);
  return args;
}
