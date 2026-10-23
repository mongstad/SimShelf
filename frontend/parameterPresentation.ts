import { parameterGroups, rowGroup, type Row } from "./parameterRows";

// A view of existing rows, never a new argv order. Keep the original index for edits.
export function parameterPresentation(rows: Row[], query: string) {
  const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  let total = 0, matches = 0;
  const sections = ["Parameters", "Flags", parameterGroups[2]].map(name => ({
    name, total: 0, required: 0, rows: [] as { row: Row; index: number }[],
  }));
  rows.forEach((row, index) => {
    const kind = rowGroup(row);
    const manual = kind === parameterGroups[2];
    const section = sections[parameterGroups.indexOf(kind)];
    const p = row.parameter;
    section.total++;
    if (!manual && p) {
      total++;
      if (p.required) section.required++;
      const text = [row.token, p.name, ...p.flags, p.help, p.type, p.type === "int" ? "integer" : p.type === "str" ? "string" : p.type,
        p.required ? "required" : "optional", p.action === "store" ? "value parameter" : "boolean flag"].join(" ").toLowerCase();
      if (!terms.every(term => text.includes(term))) return;
      matches++;
    }
    section.rows.push({row, index});
  });
  // Required controls lead each collection, without changing their source indexes.
  for (const section of sections.slice(0, 2)) {
    section.rows.sort((a, b) => Number(!!b.row.parameter?.required) - Number(!!a.row.parameter?.required));
  }
  return { total, matches, sections: sections.filter(section => section.total || section.name === parameterGroups[2]) };
}
