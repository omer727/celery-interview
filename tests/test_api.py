from conftest import upload
def test_create_category_returns_201(client):
    resp = client.post(
        "/categories",
        json={"name": "Electronics", "region": "EMEA", "type": "sales"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Electronics"
    assert body["region"] == "EMEA"
    assert body["type"] == "sales"


def test_create_duplicate_name_different_casing_returns_409(client):
    client.post("/categories", json={"name": "Books", "region": "EMEA", "type": "sales"})
    resp = client.post(
        "/categories",
        json={"name": "BOOKS", "region": "APAC", "type": "inventory"},
    )
    assert resp.status_code == 409


def test_upload_valid_xlsx_returns_201_with_sheet_count(client, make_xlsx):
    client.post("/categories", json={"name": "Sales", "region": "EMEA", "type": "sales"})
    data = make_xlsx({"Q1": [["item", "amount"], ["widget", 10]], "Q2": [["widget", 20]]})
    resp = upload(client, "Sales", data, filename="report.xlsx")
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "report.xlsx"
    assert body["sheets"] == 2


def test_upload_category_lookup_is_case_insensitive(client, make_xlsx):
    client.post("/categories", json={"name": "Sales", "region": "EMEA", "type": "sales"})
    resp = upload(client, "SALES", make_xlsx({"S1": [["a", 1]]}))
    assert resp.status_code == 201


def test_upload_to_unknown_category_returns_404(client, make_xlsx):
    data = make_xlsx({"S1": [["a", 1]]})
    resp = upload(client, "NoSuchCategory", data)
    assert resp.status_code == 404


def test_upload_non_xlsx_returns_400(client):
    client.post("/categories", json={"name": "Junk", "region": "EMEA", "type": "sales"})
    resp = upload(client, "Junk", b"this is not an excel file", filename="fake.xlsx")
    assert resp.status_code == 400


def test_sum_across_sheets_files_and_categories_of_type(client, make_xlsx):
    client.post("/categories", json={"name": "A", "region": "EMEA", "type": "sales"})
    client.post("/categories", json={"name": "B", "region": "APAC", "type": "sales"})
    client.post("/categories", json={"name": "C", "region": "EMEA", "type": "inventory"})
    upload(client, "A", make_xlsx({"S1": [[1, 2.5]], "S2": [[10]]}))
    upload(client, "A", make_xlsx({"S1": [[100]]}))
    upload(client, "B", make_xlsx({"S1": [[1000]]}))
    upload(client, "C", make_xlsx({"S1": [[99999]]}))
    resp = client.get("/sum", params={"type": "sales"})
    assert resp.status_code == 200
    assert resp.json() == {"type": "sales", "sum": 1113.5}


def test_sum_excludes_text_that_looks_numeric_and_booleans(client, make_xlsx):
    client.post("/categories", json={"name": "Typed", "region": "EMEA", "type": "typed"})
    upload(client, "Typed", make_xlsx({"S1": [["123", 5], [True, "77"]]}))
    resp = client.get("/sum", params={"type": "typed"})
    assert resp.json()["sum"] == 5


def test_sum_type_match_is_case_insensitive(client, make_xlsx):
    client.post("/categories", json={"name": "CaseCat", "region": "EMEA", "type": "Sales"})
    upload(client, "CaseCat", make_xlsx({"S1": [[7]]}))
    resp = client.get("/sum", params={"type": "sALES"})
    assert resp.json()["sum"] == 7


def test_sum_unknown_type_returns_zero(client):
    resp = client.get("/sum", params={"type": "nonexistent"})
    assert resp.status_code == 200
    assert resp.json()["sum"] == 0


def test_find_regions_returns_regions_of_matching_categories(client, make_xlsx):
    client.post("/categories", json={"name": "R1", "region": "EMEA", "type": "t"})
    client.post("/categories", json={"name": "R2", "region": "APAC", "type": "t"})
    client.post("/categories", json={"name": "R3", "region": "LATAM", "type": "t"})
    upload(client, "R1", make_xlsx({"S1": [["New York", 1]]}))
    upload(client, "R2", make_xlsx({"S1": [["yorkshire pudding"]]}))
    upload(client, "R3", make_xlsx({"S1": [["nothing relevant"]]}))
    resp = client.get("/regions", params={"search_term": "YORK"})
    assert resp.status_code == 200
    assert sorted(resp.json()["regions"]) == ["APAC", "EMEA"]


def test_find_regions_matches_numeric_cells_via_text_form(client, make_xlsx):
    client.post("/categories", json={"name": "Num", "region": "NA", "type": "t"})
    upload(client, "Num", make_xlsx({"S1": [["label", 42]]}))
    resp = client.get("/regions", params={"search_term": "42"})
    assert resp.json()["regions"] == ["NA"]


def test_find_regions_never_matches_across_cell_boundaries(client, make_xlsx):
    client.post("/categories", json={"name": "Bound", "region": "EMEA", "type": "t"})
    upload(client, "Bound", make_xlsx({"S1": [["a1", "2b"]]}))
    resp = client.get("/regions", params={"search_term": "1,2"})
    assert resp.json()["regions"] == []


def test_find_regions_dedupes_regions_case_insensitively(client, make_xlsx):
    client.post("/categories", json={"name": "D1", "region": "EMEA", "type": "t"})
    client.post("/categories", json={"name": "D2", "region": "emea", "type": "t"})
    upload(client, "D1", make_xlsx({"S1": [["needle"]]}))
    upload(client, "D2", make_xlsx({"S1": [["needle"]]}))
    resp = client.get("/regions", params={"search_term": "needle"})
    assert resp.json()["regions"] == ["EMEA"]


def test_find_regions_no_match_returns_empty_list(client, make_xlsx):
    client.post("/categories", json={"name": "E1", "region": "EMEA", "type": "t"})
    upload(client, "E1", make_xlsx({"S1": [["hay"]]}))
    resp = client.get("/regions", params={"search_term": "no-such-term"})
    assert resp.status_code == 200
    assert resp.json()["regions"] == []


def test_reupload_same_file_is_appended_and_double_counted(client, make_xlsx):
    client.post("/categories", json={"name": "Dup", "region": "EMEA", "type": "dup"})
    data = make_xlsx({"S1": [[10]]})
    assert upload(client, "Dup", data, filename="same.xlsx").status_code == 201
    assert upload(client, "Dup", data, filename="same.xlsx").status_code == 201
    resp = client.get("/sum", params={"type": "dup"})
    assert resp.json()["sum"] == 20


def test_empty_search_term_is_rejected(client):
    resp = client.get("/regions", params={"search_term": ""})
    assert resp.status_code == 422


def test_empty_category_fields_are_rejected(client):
    resp = client.post("/categories", json={"name": "", "region": "", "type": ""})
    assert resp.status_code == 422


def test_list_categories_returns_all(client):
    client.post("/categories", json={"name": "L1", "region": "EMEA", "type": "sales"})
    client.post("/categories", json={"name": "L2", "region": "APAC", "type": "inventory"})
    resp = client.get("/categories")
    assert resp.status_code == 200
    assert resp.json()["categories"] == [
        {"name": "L1", "region": "EMEA", "type": "sales"},
        {"name": "L2", "region": "APAC", "type": "inventory"},
    ]


def test_list_categories_empty(client):
    resp = client.get("/categories")
    assert resp.status_code == 200
    assert resp.json()["categories"] == []
