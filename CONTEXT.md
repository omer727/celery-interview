# Excel Categories API

A REST service that organizes uploaded Excel workbooks into categories and answers
two questions about them: the sum of all numbers per category type, and which
regions contain a given search term.

## Language

**Category**:
A named bucket that files are uploaded into. Identified by its name
(case-insensitively unique) and carrying exactly one Region and one Type.

**Category Name**:
The identity of a Category. Two names that differ only in case are the same Category.

**Type**:
A free-form label on a Category used to group categories for summing. Matched
case-insensitively; not an enum.

**Region**:
A free-form label on a Category. Regions that differ only in case are the same
Region. `find_regions` returns each matching Region once.
_Avoid_: location, area

**File**:
One uploaded Excel workbook (.xlsx) belonging to a Category. Uploads are
append-only: every upload is a new File, even with a repeated filename; there is
no update or delete.
_Avoid_: document, attachment

**Sheet**:
One worksheet within a File. All Sheets of a File participate in sums and search.

**Number**:
A cell value that Excel itself types as numeric. Text that merely looks numeric
(IDs, zip codes) is not a Number and is never summed.

**Match**:
A File matches a search term when at least one cell's text representation
contains the term as a case-insensitive substring. Numbers participate via their
text form. A term never matches across cell boundaries.
