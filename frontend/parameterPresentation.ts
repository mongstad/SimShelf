import { parameterGroups, rowGroup, type Row } from "./parameterRows";

// A view of existing rows, never a new argv order. Keep the original index for edits.
export function parameterPresentation(rows: Row[], query: string) {
  const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const groups = ["Required arguments", ...parameterGroups];
  let total = 0, matches = 0;
  const sections = groups.map(name => ({ name, rows: [] as { row: Row; index: number }[] }));
  rows.forEach((row, index) => {
    const manual = rowGroup(row) === parameterGroups[2];
    const p = row.parameter;
    if (!manual && p) {
      total++;
      const text = [row.token, p.name, ...p.flags, p.help, p.type,
        p.required ? "required" : "optional", p.action === "store" ? "value parameter" : "boolean flag"].join(" ").toLowerCase();
      if (!terms.every(term => text.includes(term))) return;
      matches++;
    }
    const group = !manual && p?.required ? groups[0] : rowGroup(row);
    sections.find(section => section.name === group)!.rows.push({row, index});
  });
  return { total, matches, sections: sections.filter(section => section.rows.length || section.name === parameterGroups[2]) };
}
