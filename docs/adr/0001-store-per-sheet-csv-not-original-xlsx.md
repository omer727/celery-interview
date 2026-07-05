# Store uploaded workbooks as per-sheet CSV, not the original xlsx bytes

Uploaded .xlsx files are converted at upload time into one CSV per sheet and the
original bytes are discarded — styles, formulas, and formatting are irrelevant to
the API's two queries (sum and search), so we keep only content. Because CSV
erases Excel's cell typing, everything that depends on types is derived during
conversion while the workbook is still open: each sheet's numeric sum (Excel's
own cell types decide what is a Number) and its lowercased per-cell search text.
The trade-off accepted: if query semantics ever change in a way that needs
information CSV doesn't carry (formulas, types beyond what we derived), the
originals cannot be re-read — files would have to be re-uploaded. The rejected
alternative was storing the raw xlsx BLOBs and parsing at query time, which
keeps all information but re-does O(cells) work on every query and forces
number-ness to be re-inferred from text.
