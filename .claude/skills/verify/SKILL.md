---
name: verify
description: Build, launch, and drive the Excel Categories API end-to-end for verification.
---

# Verifying the Excel Categories API

## Launch

```bash
.venv/bin/pip install -q -r requirements.txt   # once
rm -f data.db                                  # start clean; data.db is the real store
.venv/bin/uvicorn main:app --port 8734 &       # Swagger at /docs
```

## Drive (flows worth exercising)

```bash
B=http://127.0.0.1:8734
curl -X POST $B/categories -H 'Content-Type: application/json' \
  -d '{"name":"US Sales","region":"North America","type":"sales"}'
curl -X POST "$B/categories/US%20Sales/files" -F "file=@test_files/sales_report.xlsx"
curl "$B/sum?type=SALES"            # case-insensitive type; expect the known fixture sums
curl "$B/regions?search_term=york"  # substring, case-insensitive
```

Fixture sums (from make_test_files.py): sales_report=700.0, tricky_types=30.0, city_offices=59.0.

Probes that matter: duplicate name in different casing → 409; upload garbage bytes → 400; unknown category → 404; `search_term=1,2` after uploading city_offices → `[]` (no cross-cell match); empty `search_term` → 422; restart the server and re-query to confirm SQLite persistence.

## Cleanup

`pkill -f "uvicorn main:app --port 8734"; rm -f data.db`
