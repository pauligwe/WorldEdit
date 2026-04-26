interface PropItem {
  name?: string;
  vendor?: string;
  url?: string;
  price_estimate_usd?: number;
  category?: string;
  image_url?: string;
}

export function buildPropsCsv(items: PropItem[]): string {
  const headers = ["name", "category", "vendor", "price_usd", "url", "image_url"];
  const rows = [headers.join(",")];
  for (const it of items) {
    rows.push(
      [
        csv(it.name),
        csv(it.category),
        csv(it.vendor),
        it.price_estimate_usd != null ? String(it.price_estimate_usd) : "",
        csv(it.url),
        csv(it.image_url),
      ].join(","),
    );
  }
  return rows.join("\n");
}

function csv(v: unknown): string {
  if (v == null) return "";
  const s = String(v);
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}
