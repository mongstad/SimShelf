import type { OutputMapping } from "./types";

/** Empty fixed-path rows are drafts, never omitted from saved or launched settings. */
export function incompleteOutputMappings(mappings: OutputMapping[]) {
  return mappings.flatMap((m, index) => m.argument_index === null && m.value === "" ? [index] : []);
}

/** Suggestions require the user's explicit declaration of file/directory meaning. */
export function outputCandidates(args: string[]) {
  const result: { index: number; flag: string; format: "token" | "equals" }[] =
    [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--") break;
    const flag = args[i].split("=", 1)[0];
    if (!["--wvz", "--output", "--output-dir"].includes(flag)) continue;
    if (args[i].includes("=")) {
      result.push({ index: i, flag, format: "equals" });
    } else if (i + 1 < args.length && !args[i + 1].startsWith("--")) {
      result.push({ index: ++i, flag, format: "token" });
    }
  }
  return result;
}
