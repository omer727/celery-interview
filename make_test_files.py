"""Generate the .xlsx files used to test the API (attached to the submission).

Each file documents an edge case the implementation handles:
  sales_report.xlsx   - multi-sheet workbook: ALL sheets count toward sums
  tricky_types.xlsx   - text that looks numeric ("123"), booleans, dates:
                        only cells Excel types as numeric are summed
  city_offices.xlsx   - search-term material: terms mid-cell ("New York"),
                        numeric cells searchable ("42"), and adjacent cells
                        ("a1" | "2b") proving no cross-cell match for "1,2"

Run: python make_test_files.py   (writes into test_files/)
"""

from pathlib import Path

from openpyxl import Workbook

OUT_DIR = Path(__file__).parent / "test_files"


def build(filename: str, sheets: dict[str, list[list]]) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(name)
        for row in rows:
            ws.append(row)
    wb.save(OUT_DIR / filename)
    print(f"wrote {OUT_DIR / filename}")


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)

    build(
        "sales_report.xlsx",
        {
            "Q1": [["item", "amount"], ["widget", 100], ["gadget", 250.5]],
            "Q2": [["item", "amount"], ["widget", 300], ["gadget", 49.5]],
        },
    )  # numeric sum: 700.0

    build(
        "tricky_types.xlsx",
        {
            "Sheet1": [
                ["id (text)", "quantity (number)", "in stock (bool)"],
                ["123", 10, True],
                ["456", 20, False],
            ],
        },
    )  # numeric sum: 30.0 — "123"/"456" are text, booleans are not Numbers

    build(
        "city_offices.xlsx",
        {
            "Offices": [
                ["city", "headcount"],
                ["New York", 42],
                ["London", 17],
            ],
            "Boundary": [["a1", "2b"]],  # search "1,2" must NOT match
        },
    )  # numeric sum: 59.0 + boundary sheet 0


if __name__ == "__main__":
    main()
