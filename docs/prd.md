---
title: Excel Categories API
labels: [ready-for-agent]
status: ready
---

# PRD: Excel Categories API

Domain language: see [CONTEXT.md](../CONTEXT.md). Capitalized terms (Category,
File, Sheet, Number, Match, Region, Type) are used as defined in the glossary.
Rationale and rejected alternatives for each decision live in
[docs/adr/](./adr/); this PRD states only the *what* and links the *why*.

## Problem Statement

A reviewer at Celery needs to evaluate a take-home assignment: a simple REST API
that organizes uploaded Excel workbooks into categories and answers two
questions about them — the sum of all Numbers across a Type, and which Regions
contain a given search term. The reviewer will run the service locally, poke it
through FastAPI's Swagger UI, and discuss it in a 15-minute call. The submission
must run out of the box, read clearly, and defend every design decision in
comments.

## Solution

A FastAPI service backed by a single SQLite database. Uploaded .xlsx workbooks
are converted at upload time into one CSV per Sheet; each Sheet's numeric sum
and lowercased search text are derived during conversion, while Excel's own cell
typing is still available. The two query endpoints then reduce to single SQL
queries. Four endpoints, RESTful URLs, case-insensitive matching everywhere,
append-only uploads.

## User Stories

1. As an API consumer, I want to create a Category with a name, Region, and Type, so that I have a bucket to upload Files into.
2. As an API consumer, I want creating a Category whose name already exists (in any casing) to fail with 409 Conflict, so that Category identity stays unambiguous.
3. As an API consumer, I want to upload an .xlsx File to a Category by name, so that its contents count toward that Category's Type sums and Region search.
4. As an API consumer, I want uploading to a nonexistent Category to fail with 404, so that typos don't silently create or orphan data.
5. As an API consumer, I want uploading a corrupt or non-.xlsx file to fail with 400 and store nothing, so that a bad upload never partially pollutes query results.
6. As an API consumer, I want to upload the same filename twice and get two Files, so that legitimate same-named files are never rejected or silently overwritten.
7. As an API consumer, I want every Sheet of a multi-sheet workbook included in sums and search, so that "all numbers in all excel files" is literally true.
8. As an API consumer, I want sum_type to return the sum of all Numbers in all Files in all Categories of a Type, so that I can aggregate across the whole Type at once.
9. As an API consumer, I want sum_type to match the Type case-insensitively, so that "Sales" and "sales" aggregate the same categories.
10. As an API consumer, I want sum_type of a Type no Category has to return 200 with sum 0, so that an empty aggregate is an answer, not an error.
11. As an API consumer, I want only values Excel itself types as numeric to be summed, so that IDs and zip codes stored as text never corrupt the total.
12. As an API consumer, I want find_regions to return the Regions of Categories having at least one File that Matches the search term, so that I can locate where a term appears.
13. As an API consumer, I want the Match to be a case-insensitive substring within a single cell, so that "york" finds "New York" but a term never falsely matches across two adjacent cells.
14. As an API consumer, I want numeric cells to be searchable via their text form, so that searching "42" finds a cell holding the number 42.
15. As an API consumer, I want find_regions to return each Region once, deduplicated case-insensitively (first-stored casing wins), so that "EMEA" and "emea" don't appear as two regions.
16. As an API consumer, I want find_regions with no matches to return 200 with an empty list, so that a miss is distinguishable from a failure.
17. As the reviewer, I want the service to start with a plain `uvicorn` command after a pip install, so that evaluating it takes minutes.
18. As the reviewer, I want all four endpoints usable from the auto-generated Swagger UI including the file-upload widget, so that I can test without writing a client.
19. As the reviewer, I want data to survive a server restart, so that my Swagger session doesn't reset every time the process bounces.
20. As the reviewer, I want design decisions and would-do-differently notes as code comments, so that the 15-minute call has anchors.
21. As the candidate, I want generated test .xlsx files covering the edge cases (multi-sheet, numeric-looking text, search-term placement), so that I can attach them to the submission email as required.
22. As the candidate, I want an automated test suite driving the API end-to-end, so that I can verify the whole flow with one command before submitting and during the call.
23. As the candidate, I want a README with install and run steps, so that the "your code is expected to run" requirement is met explicitly.

## Implementation Decisions

- **Stack**: Python, FastAPI, `openpyxl` for parsing. Dependencies: fastapi, uvicorn, openpyxl, python-multipart, pytest.
- **Persistence**: single SQLite database file, schema created on startup — [ADR 0002](./adr/0002-sqlite-for-persistence.md).
- **DB access**: stdlib `sqlite3` with raw SQL, no ORM — [ADR 0007](./adr/0007-stdlib-sqlite3-raw-sql-no-orm.md).
- **Storage model**: originals discarded at upload; one CSV stored per Sheet — [ADR 0001](./adr/0001-store-per-sheet-csv-not-original-xlsx.md).
- **Query implementation**: each Sheet's `numeric_sum` and lowercased `search_text` (cell values joined by a delimiter that cannot appear in a search term) are derived at upload, so sum_type is a single `SELECT SUM(numeric_sum)` join and find_regions a `LIKE` over `search_text` with distinct-Region reduction — [ADR 0003](./adr/0003-derive-sum-and-search-text-at-upload.md).
- **Case-insensitivity is the single global rule**: name uniqueness, Type matching, Region dedup, and search Match; stored values keep original casing — [ADR 0004](./adr/0004-case-insensitive-everywhere.md).
- **Uploads are append-only**: no update/delete; a repeated filename is a new File — [ADR 0005](./adr/0005-append-only-uploads.md).
- **Validation by parsing, not extension**: .xlsx only, all-or-nothing on failure — [ADR 0008](./adr/0008-validate-by-parsing-xlsx-only.md).
- **API contract** (RESTful resources, docstrings map to the assignment's function names — [ADR 0006](./adr/0006-restful-urls-not-spec-rpc-names.md)):
  - `POST /categories` (name, region, type) → 201; 409 on duplicate name
  - `POST /categories/{name}/files` (multipart file) → 201; 404 unknown Category; 400 unparseable file
  - `GET /sum?type=X` → 200 `{type, sum}`; sum 0 for unknown Type
  - `GET /regions?search_term=Y` → 200 `{regions: [...]}`; empty list on no Match
- **Module layout**: three small modules — routes, Excel conversion, database — plus a test-file generator script, tests, README, requirements.txt.
- **Assignment-mandated commentary**: design decisions and would-do-differently notes (production DB + object storage, content-hash dedupe, type as a lookup table) written as code comments where the decision lives.

## Testing Decisions

- **Seam: the HTTP API boundary only.** Tests drive all four endpoints through FastAPI's TestClient with real generated .xlsx bytes and assert only on status codes and JSON bodies — external behavior, never internals. The Excel-conversion and SQL layers are implementation details fully observable through sum/search responses, so they get no direct unit tests; this keeps tests valid across internal refactors (e.g. changing the CSV storage).
- **One new seam required**: the app must accept an injectable database location (app factory or settings), so tests run against a temporary SQLite file instead of the real one.
- **Test fixtures are generated, not hand-made**: a generator script produces the .xlsx files (multi-sheet workbook, text-that-looks-numeric, search terms placed mid-cell and adjacent-cell to prove boundary behavior, empty sheet). The same files double as the email attachments the assignment requires.
- **Cases to cover**: happy path per endpoint; 409 duplicate name (different casing); 404 unknown category; 400 corrupt upload stores nothing; multi-sheet summing; text "123" excluded from sum; case-insensitive type match; substring Match within a cell; no cross-cell false Match; region dedup; empty results return 0 / [].
- **Prior art**: none — greenfield repo; this suite establishes the pattern.

## Out of Scope

- Update or delete for Categories and Files; pagination. (A read-only
  `GET /categories` listing was later added by user request as a Swagger
  convenience — it remains outside the assignment's four endpoints.)
- Authentication, authorization, rate limiting.
- Legacy .xls, CSV, or any non-.xlsx input format.
- Formula evaluation (openpyxl returns cached values; we take what the workbook stored).
- Concurrent-writer robustness beyond SQLite's defaults.
- Deployment concerns (Docker, hosting); the deliverable runs locally via uvicorn.
- Recovering original workbook bytes after upload (accepted in [ADR 0001](./adr/0001-store-per-sheet-csv-not-original-xlsx.md)).

## Further Notes

- Submission checklist from the assignment: email code to noam@celery.cc, attach the generated test .xlsx files, include install steps (README), be ready for a 15-minute call.
- The precompute-at-upload design is the intended answer to the assignment's "make your code as clear and efficient as possible" hint — worth saying out loud on the call.
- Swagger UI (`/docs`) is the primary demo surface; endpoint summaries and examples should read well there.
