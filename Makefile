# Task runner for the Excel Categories API.
# All targets use the project venv directly — no activation needed.

VENV := .venv/bin

.PHONY: install run test files clean help

help:  ## show available tasks
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

install:  ## create venv and install dependencies
	python3 -m venv .venv
	$(VENV)/pip install -r requirements.txt

run:  ## start the API with auto-reload (Swagger at http://127.0.0.1:8000/docs)
	$(VENV)/uvicorn main:app --reload

test:  ## run the test suite
	$(VENV)/python -m pytest

files:  ## regenerate the test .xlsx files in test_files/
	$(VENV)/python make_test_files.py

clean:  ## remove the local database (fresh demo state)
	rm -f data.db
