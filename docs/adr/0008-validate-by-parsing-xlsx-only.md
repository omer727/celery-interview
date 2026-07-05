# Validate uploads by parsing; .xlsx only

A file is a valid upload iff openpyxl can open it — extension and content-type
are ignored as evidence, since both lie. Only .xlsx/.xlsm is accepted: legacy
.xls would require a second parser (xlrd) and format branch for a format the
reviewer almost certainly won't send, and CSV input carries no cell types,
which would reopen the number-inference problem closed by
[ADR 0001](./0001-store-per-sheet-csv-not-original-xlsx.md). Uploads are
all-or-nothing: a parse failure returns 400 and stores nothing, so a bad file
can never partially pollute sums or search.
