# Derive sums and search text at upload, not at query time

Each Sheet's numeric sum and lowercased search text are computed once during
upload conversion and stored, so `sum_type` is a `SELECT SUM(...)` join and
`find_regions` is a `LIKE` scan — no Excel or CSV parsing ever happens at query
time. This is safe because uploads are append-only ([ADR 0005](./0005-append-only-uploads.md)):
derived values can never go stale. It is also required, not just faster —
Excel's cell typing decides what counts as a Number, and that information only
exists while the workbook is open ([ADR 0001](./0001-store-per-sheet-csv-not-original-xlsx.md)).
The rejected alternative, parsing stored content on every query, repeats
O(cells) work per call and would force number-ness to be re-inferred from text.
