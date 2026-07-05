# Uploads are append-only; filename is not identity

Every upload creates a new File, even with a repeated filename — nothing is
overwritten, rejected as duplicate, or deletable. The spec defines no update or
delete, so inventing replace-on-same-name semantics would add an unrequested
behavior whose failure mode (a sum silently changing after a re-upload) is
confusing to verify. Consequence: uploading the same workbook twice double-counts
it in sums — accepted; production would want content-hash dedupe or versioning.
This immutability is also what makes precomputed derived values safe
([ADR 0003](./0003-derive-sum-and-search-text-at-upload.md)).
