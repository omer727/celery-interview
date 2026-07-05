# Manual test plan — Excel Categories API

A step-by-step checklist for exercising every endpoint and documented edge
case by hand, either via the Swagger UI (`/docs`) or `curl`. Uses the fixture
files in `test_files/` (see `make_test_files.py` for what each one contains).

## Setup

```bash
.venv/bin/pip install -q -r requirements.txt   # once
rm -f data.db                                  # start clean
.venv/bin/uvicorn main:app --port 8734 &
B=http://127.0.0.1:8734
```

Fixture sums: `sales_report.xlsx` = 700.0, `tricky_types.xlsx` = 30.0,
`city_offices.xlsx` = 59.0.

Tick each box as you confirm the actual result matches "Expect".

## 1. `POST /categories` — create_category

- [ ] Create a category:
  ```bash
  curl -i -X POST $B/categories -H 'Content-Type: application/json' \
    -d '{"name":"US Sales","region":"North America","type":"sales"}'
  ```
  Expect: `201`, body echoes name/region/type.

- [ ] Create a second, different category (for later sum/region tests):
  ```bash
  curl -i -X POST $B/categories -H 'Content-Type: application/json' \
    -d '{"name":"City Offices","region":"Europe","type":"ops"}'
  ```
  Expect: `201`.

- [ ] Duplicate name, same case:
  ```bash
  curl -i -X POST $B/categories -H 'Content-Type: application/json' \
    -d '{"name":"US Sales","region":"EMEA","type":"other"}'
  ```
  Expect: `409`.

- [ ] Duplicate name, different case (`us sales`):
  ```bash
  curl -i -X POST $B/categories -H 'Content-Type: application/json' \
    -d '{"name":"us sales","region":"EMEA","type":"other"}'
  ```
  Expect: `409` (name uniqueness is case-insensitive).

- [ ] Empty field (name/region/type):
  ```bash
  curl -i -X POST $B/categories -H 'Content-Type: application/json' \
    -d '{"name":"","region":"","type":""}'
  ```
  Expect: `422`.

- [ ] Missing field entirely:
  ```bash
  curl -i -X POST $B/categories -H 'Content-Type: application/json' \
    -d '{"name":"NoType","region":"EMEA"}'
  ```
  Expect: `422`.

## 2. `GET /categories` — list (extra endpoint)

- [ ] ```bash
  curl -i $B/categories
  ```
  Expect: `200`, JSON array containing "US Sales" and "City Offices" with
  their original region/type.

## 3. `POST /categories/{name}/files` — upload_file

- [ ] Upload a valid multi-sheet workbook:
  ```bash
  curl -i -X POST "$B/categories/US%20Sales/files" \
    -F "file=@test_files/sales_report.xlsx"
  ```
  Expect: `201`, `sheets` count matches the workbook (2 for sales_report).

- [ ] Upload to an unknown category:
  ```bash
  curl -i -X POST "$B/categories/Nope/files" \
    -F "file=@test_files/sales_report.xlsx"
  ```
  Expect: `404`.

- [ ] Upload a non-xlsx / garbage file:
  ```bash
  echo "not an excel file" > /tmp/fake.xlsx
  curl -i -X POST "$B/categories/US%20Sales/files" -F "file=@/tmp/fake.xlsx"
  ```
  Expect: `400`.

- [ ] Re-upload the same file again (append-only, no dedup):
  ```bash
  curl -i -X POST "$B/categories/US%20Sales/files" \
    -F "file=@test_files/sales_report.xlsx"
  ```
  Expect: `201` again — this category's sum should double once you check
  step 4 (700 + 700 = 1400).

- [ ] Upload `tricky_types.xlsx` and `city_offices.xlsx` into "City Offices"
  (used for sum/search edge cases below):
  ```bash
  curl -i -X POST "$B/categories/City%20Offices/files" \
    -F "file=@test_files/tricky_types.xlsx"
  curl -i -X POST "$B/categories/City%20Offices/files" \
    -F "file=@test_files/city_offices.xlsx"
  ```
  Expect: both `201`.

## 4. `GET /sum` — sum_type

- [ ] Sum for "US Sales" type (after the double-upload in step 3):
  ```bash
  curl -i "$B/sum?type=sales"
  ```
  Expect: `200`, `{"type":"sales","sum":1400.0}`.

- [ ] Case-insensitive type match:
  ```bash
  curl -i "$B/sum?type=SALES"
  ```
  Expect: same result as above.

- [ ] Sum for "ops" type — checks tricky_types + city_offices, i.e. that
  text-that-looks-numeric ("123") and booleans are excluded, and multi-sheet
  workbooks fully counted:
  ```bash
  curl -i "$B/sum?type=ops"
  ```
  Expect: `200`, `{"type":"ops","sum":89.0}` (30.0 + 59.0).

- [ ] Unknown/nonexistent type:
  ```bash
  curl -i "$B/sum?type=doesnotexist"
  ```
  Expect: `200`, `{"type":"doesnotexist","sum":0}` (not an error).

- [ ] Missing `type` query param:
  ```bash
  curl -i "$B/sum"
  ```
  Expect: `422`.

## 5. `GET /regions` — find_regions

- [ ] Substring match, case-insensitive ("york" → "New York" cell in
  city_offices.xlsx):
  ```bash
  curl -i "$B/regions?search_term=york"
  ```
  Expect: `200`, `{"regions":["Europe"]}` (the region of "City Offices").

- [ ] Numeric cell matched via its text form (city_offices has `42` and `17`):
  ```bash
  curl -i "$B/regions?search_term=42"
  ```
  Expect: `200`, includes "Europe".

- [ ] No cross-cell-boundary match — city_offices' "Boundary" sheet has
  adjacent cells `a1` | `2b`; searching for `1,2` must not match:
  ```bash
  curl -i "$B/regions?search_term=1,2"
  ```
  Expect: `200`, `{"regions":[]}`.

- [ ] No match at all:
  ```bash
  curl -i "$B/regions?search_term=zzz_nonexistent"
  ```
  Expect: `200`, `{"regions":[]}`.

- [ ] Empty search term is rejected:
  ```bash
  curl -i "$B/regions?search_term="
  ```
  Expect: `422`.

- [ ] Missing `search_term` param entirely:
  ```bash
  curl -i "$B/regions"
  ```
  Expect: `422`.

- [ ] Region dedup, case-insensitive: create two categories whose regions
  differ only in case, upload a matching file to each, confirm the region
  appears once in the result:
  ```bash
  curl -s -X POST $B/categories -H 'Content-Type: application/json' \
    -d '{"name":"Dup1","region":"EMEA","type":"t"}' >/dev/null
  curl -s -X POST $B/categories -H 'Content-Type: application/json' \
    -d '{"name":"Dup2","region":"emea","type":"t"}' >/dev/null
  .venv/bin/python3 - <<'EOF'
  from openpyxl import Workbook
  wb = Workbook()
  wb.active.append(["needle"])
  wb.save("/tmp/needle.xlsx")
  EOF
  curl -s -X POST "$B/categories/Dup1/files" -F "file=@/tmp/needle.xlsx"
  curl -s -X POST "$B/categories/Dup2/files" -F "file=@/tmp/needle.xlsx"
  curl -i "$B/regions?search_term=needle"
  ```
  Expect: `{"regions":["EMEA"]}` — one entry, first-stored casing.

## 6. Persistence

- [ ] Restart the server and re-query without re-uploading anything:
  ```bash
  pkill -f "uvicorn main:app --port 8734"
  .venv/bin/uvicorn main:app --port 8734 &
  curl -i "$B/sum?type=sales"
  curl -i "$B/categories"
  ```
  Expect: identical results to before the restart — SQLite persisted to
  `data.db`.

## 7. Swagger UI sanity check (optional, exercises the file-upload widget)

- [ ] Open `http://127.0.0.1:8734/docs`, use "Try it out" on
  `POST /categories/{name}/files` to upload `test_files/sales_report.xlsx`
  through the browser widget rather than curl. Expect the same `201` /
  sheet-count response.

## Cleanup

```bash
pkill -f "uvicorn main:app --port 8734"
rm -f data.db /tmp/fake.xlsx
```
