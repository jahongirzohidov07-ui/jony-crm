import * as XLSX from "xlsx";

/** Rough column-width heuristic so exported sheets aren't all crammed into
 * default-width columns - based on the longest value (or header) per key. */
function autoColumnWidths(rows: Record<string, unknown>[]) {
  if (rows.length === 0) return [];
  const keys = Object.keys(rows[0]);
  return keys.map((key) => {
    const longest = Math.max(
      key.length,
      ...rows.map((r) => String(r[key] ?? "").length)
    );
    return { wch: Math.min(Math.max(longest + 2, 10), 42) };
  });
}

/**
 * Exports an array of plain objects to a downloadable .xlsx file.
 * Keys of the first row become the header row, in order.
 */
export function exportToExcel(
  filename: string,
  sheetName: string,
  rows: Record<string, unknown>[]
) {
  const ws = XLSX.utils.json_to_sheet(rows);
  ws["!cols"] = autoColumnWidths(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, sheetName.slice(0, 31));
  const safeName = filename.endsWith(".xlsx") ? filename : `${filename}.xlsx`;
  XLSX.writeFile(wb, safeName);
}

/** Exports several named sheets into a single workbook. */
export function exportSheetsToExcel(
  filename: string,
  sheets: { name: string; rows: Record<string, unknown>[] }[]
) {
  const wb = XLSX.utils.book_new();
  for (const sheet of sheets) {
    const ws = XLSX.utils.json_to_sheet(sheet.rows);
    ws["!cols"] = autoColumnWidths(sheet.rows);
    XLSX.utils.book_append_sheet(wb, ws, sheet.name.slice(0, 31));
  }
  const safeName = filename.endsWith(".xlsx") ? filename : `${filename}.xlsx`;
  XLSX.writeFile(wb, safeName);
}
