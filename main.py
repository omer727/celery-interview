"""Excel Categories API — FastAPI routes.

Assignment endpoint mapping (ADR 0006: RESTful URLs over the spec's RPC names):
  create_category -> POST /categories
  upload_file     -> POST /categories/{name}/files
  sum_type        -> GET /sum?type=
  find_regions    -> GET /regions?search_term=
"""

import sqlite3

from fastapi import FastAPI, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

import db
import excel

DEFAULT_DB_PATH = "data.db"


class CategoryIn(BaseModel):
    # min_length=1: empty identity/label strings are never meaningful here.
    name: str = Field(min_length=1)
    region: str = Field(min_length=1)
    type: str = Field(min_length=1)


def create_app(db_path: str = DEFAULT_DB_PATH) -> FastAPI:
    # App factory so tests can point the app at a temporary database.
    app = FastAPI(title="Excel Categories API")

    @app.post("/categories", status_code=201)
    def create_category(category: CategoryIn):
        """create_category(category_name, region, type) from the assignment."""
        with db.connect(db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO categories (name, region, type) VALUES (?, ?, ?)",
                    (category.name, category.region, category.type),
                )
            except sqlite3.IntegrityError:
                # Name uniqueness is case-insensitive (ADR 0004); the UNIQUE
                # NOCASE constraint is the single source of truth for it.
                raise HTTPException(409, f"category '{category.name}' already exists")
        return {"name": category.name, "region": category.region, "type": category.type}

    @app.get("/categories")
    def list_categories():
        """List all categories (extra endpoint beyond the assignment,
        added for convenience when exploring via Swagger)."""
        with db.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT name, region, type FROM categories ORDER BY id"
            ).fetchall()
        return {"categories": [dict(row) for row in rows]}

    @app.post("/categories/{name}/files", status_code=201)
    async def upload_file(name: str, file: UploadFile):
        """upload_file(category_name, file) from the assignment."""
        data = await file.read()
        # ADR 0008: a file is a valid .xlsx iff openpyxl opens it — extension
        # and content-type lie. Parsing before any INSERT makes the upload
        # all-or-nothing: a bad file can never partially pollute query results.
        # Broad except is deliberate: openpyxl raises many exception types for
        # malformed input (BadZipFile, InvalidFileException, KeyError, ...).
        try:
            sheets = excel.workbook_to_sheets(data)
        except Exception:
            raise HTTPException(400, "file is not a readable .xlsx workbook")
        with db.connect(db_path) as conn:
            category = conn.execute(
                "SELECT id FROM categories WHERE name = ?", (name,)
            ).fetchone()
            if category is None:
                raise HTTPException(404, f"category '{name}' not found")
            cur = conn.execute(
                "INSERT INTO files (category_id, filename) VALUES (?, ?)",
                (category["id"], file.filename),
            )
            conn.executemany(
                "INSERT INTO sheets (file_id, sheet_name, csv_content, numeric_sum, search_text)"
                " VALUES (?, ?, ?, ?, ?)",
                [(cur.lastrowid, *sheet) for sheet in sheets],
            )
        return {"filename": file.filename, "sheets": len(sheets)}

    @app.get("/sum")
    def sum_type(type: str):
        """sum_type(type) from the assignment: sum of all numbers in all
        excel files in categories of this type."""
        with db.connect(db_path) as conn:
            # type comparison is case-insensitive via the column's NOCASE
            # collation (ADR 0004). COALESCE: sum over an empty set is 0,
            # a valid answer, not an error (see PRD).
            row = conn.execute(
                """
                SELECT COALESCE(SUM(s.numeric_sum), 0) AS total
                FROM sheets s
                JOIN files f ON f.id = s.file_id
                JOIN categories c ON c.id = f.category_id
                WHERE c.type = ?
                """,
                (type,),
            ).fetchone()
        return {"type": type, "sum": row["total"]}

    @app.get("/regions")
    def find_regions(search_term: str = Query(min_length=1)):
        """find_regions(search_term) from the assignment: regions of
        categories with at least one file containing the search term."""
        # min_length=1: the empty string is a substring of everything, so an
        # empty term would match every file — reject it instead.
        with db.connect(db_path) as conn:
            # instr() instead of LIKE: no wildcard/escaping pitfalls if the
            # term contains % or _. Both sides are lowercased in Python
            # (search_text at upload, the term here) for one consistent
            # case-insensitivity rule (ADR 0004).
            rows = conn.execute(
                """
                SELECT DISTINCT c.id, c.region
                FROM categories c
                JOIN files f ON f.category_id = c.id
                JOIN sheets s ON s.file_id = f.id
                WHERE instr(s.search_text, ?) > 0
                ORDER BY c.id
                """,
                (search_term.lower(),),
            ).fetchall()
        # Regions differing only in case are one Region (ADR 0004);
        # first-stored casing wins.
        regions: dict[str, str] = {}
        for row in rows:
            regions.setdefault(row["region"].lower(), row["region"])
        return {"regions": list(regions.values())}

    return app


app = create_app()
