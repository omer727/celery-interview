# RESTful resource URLs instead of the spec's RPC names

The assignment names its endpoints RPC-style (`create_category`, `upload_file`,
`sum_type`, `find_regions`) but asks for "a simple REST API" — we follow the
REST half: `POST /categories`, `POST /categories/{name}/files`, `GET /sum?type=`,
`GET /regions?search_term=`. Endpoint docstrings reference the spec's function
names so a reviewer can map them instantly in Swagger. The rejected alternative
— using the spec names literally as paths — is zero-mapping-effort but is
RPC-over-HTTP in a task that explicitly says REST.
