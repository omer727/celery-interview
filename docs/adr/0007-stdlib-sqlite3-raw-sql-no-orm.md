# stdlib sqlite3 with raw SQL, no ORM

Database access uses Python's stdlib `sqlite3` and handwritten SQL rather than
the FastAPI-idiomatic SQLModel/SQLAlchemy. For two tables and four queries, the
ORM's session management and model machinery outweigh the task, add a
dependency, and hide the very thing worth showing — that `sum_type` is
literally one `SELECT SUM`. A reasonable reader of a FastAPI project would
expect an ORM, so this deviation is deliberate: transparency over idiom at this
scale.
