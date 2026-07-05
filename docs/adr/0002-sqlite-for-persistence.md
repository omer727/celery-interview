# SQLite for persistence

For a take-home reviewed via a local Swagger session, in-memory dicts would have
satisfied the spec with less code — but we chose SQLite so data survives server
restarts during review, and so derived per-Sheet values (numeric sum, search
text) have a natural home where the two query endpoints become single SQL
statements. The rejected alternatives were in-memory storage (loses everything
on restart, and the reviewer's session with it) and a client-server database
(setup steps for the reviewer, contradicting "your code is expected to run").
