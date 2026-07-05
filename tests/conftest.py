import io

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from main import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def make_xlsx():
    """Build an in-memory .xlsx: {sheet_name: [row, row, ...]} -> bytes."""

    def _make(sheets):
        wb = Workbook()
        wb.remove(wb.active)
        for name, rows in sheets.items():
            ws = wb.create_sheet(name)
            for row in rows:
                ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    return _make


def upload(client, category, xlsx_bytes, filename="test.xlsx"):
    return client.post(
        f"/categories/{category}/files",
        files={"file": (filename, xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
