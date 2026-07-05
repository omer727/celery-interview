# Case-insensitivity is one global rule

Every string comparison in the API is case-insensitive: Category-name
uniqueness, Type matching in `sum_type`, Region deduplication in
`find_regions`, and search-term Matching. Stored values keep their original
casing for display; Regions differing only in case are one Region, returned in
first-stored casing. One uniform rule was chosen over per-field rules (e.g.
exact type match but insensitive search) because a mixed scheme is more to
explain and more surprising when a Swagger demo query like `sum_type("Sales")`
silently misses `sales`.
