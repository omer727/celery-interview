# Excel Categories API

A small FastAPI service that organizes uploaded Excel workbooks into categories
and answers two questions about them: the sum of all numbers per category type,
and which regions contain a given search term.

## Install & run

Requires Python 3.9+.

```bash
make install   # create venv + install dependencies
make run       # start the API with auto-reload
```

(`make help` lists all tasks: `test`, `clean`. Without make:
`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`,
then `.venv/bin/uvicorn main:app --reload`.)

Then open the Swagger UI at http://127.0.0.1:8000/docs — all four endpoints
are usable from there, including the file-upload widget.

Data persists in `data.db` (SQLite, created on first request).

## Endpoints

Assignment name | HTTP | Notes
--- | --- | ---
`create_category(name, region, type)` | `POST /categories` | 409 if the name exists (case-insensitive)
`upload_file(category_name, file)` | `POST /categories/{name}/files` | .xlsx only; 404 unknown category; 400 unreadable file
`sum_type(type)` | `GET /sum?type=X` | sum of all numbers in all files of that type; 0 if none
`find_regions(search_term)` | `GET /regions?search_term=Y` | distinct regions of categories with a matching file
— (extra) | `GET /categories` | list all categories; convenience for exploring via Swagger

Semantics in one paragraph: all matching is **case-insensitive** (category-name
uniqueness, type matching, search). A "number" is what Excel itself types as
numeric — text like `"123"` is never summed; all sheets of a workbook count.
A file "contains" a term when some cell's text contains it as a substring —
a term never matches across two adjacent cells. Uploads are append-only:
re-uploading the same file counts it twice.

## Design in one paragraph

Workbooks are converted at upload into one CSV per sheet; each sheet's numeric
sum and lowercased search text are derived during conversion, while Excel's
cell typing is still available (CSV erases it). Everything is stored in a
single SQLite database, so both query endpoints are single SQL statements and
no Excel file is ever re-parsed at query time. Decision rationale lives in
`docs/adr/`; domain vocabulary in `CONTEXT.md`.

## Tests

```bash
make test
```

The suite drives all four endpoints end-to-end through FastAPI's TestClient
against a temporary database, building its Excel fixtures in-memory. The
attached Excel files in `test_files/` are ready-made for manual uploads via
Swagger; each one documents an edge case (multi-sheet sums, numeric-looking
text, search-term boundaries).

## Future development

Directions deliberately left out of scope (several are the flip side of
decisions recorded in `docs/adr/`):

- **File management** — uploads are append-only by design ([ADR 0005](docs/adr/0005-append-only-uploads.md)):
  no list, replace, or delete for files, and no delete for categories. A
  `GET /categories/{name}/files` plus `DELETE` endpoints would be the natural
  next resources.
- **Legacy `.xls` support** — only `.xlsx`/`.xlsm` is accepted
  ([ADR 0008](docs/adr/0008-validate-by-parsing-xlsx-only.md)); supporting
  `.xls` means adding a second parser (`xlrd`) and a format branch.
- **Scaling the store** — SQLite fits a single-process review setup
  ([ADR 0002](docs/adr/0002-sqlite-for-persistence.md)); concurrent writers or
  multiple app instances would call for Postgres, and the raw-SQL layer in
  `db.py` is small enough to port directly.
- **Large uploads** — workbooks are parsed in memory; very large files would
  need streaming reads and a size limit on the upload endpoint.
- **Search beyond substring** — `find_regions` is a `LIKE` scan over derived
  text ([ADR 0003](docs/adr/0003-derive-sum-and-search-text-at-upload.md));
  word-boundary or full-text search (SQLite FTS5) would slot into the same
  derived-at-upload design.
- **Operational hardening** — authentication, rate limiting, pagination on
  `GET /categories`, and structured logging are all absent, as befits a
  take-home, and all standard FastAPI additions.
