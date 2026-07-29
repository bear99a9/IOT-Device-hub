# IoT Device Management Backend pr version

### Planning

- Node vs FastAPI:
  - \+ Node +: consistent language across the front and backend
  - \+ Node +: event loop / async I/O model well suited for a smart home's frequent and concurrent events.
  - \+ FastAPI +: auto generated docs, easy to review/understand quickly
  - \+ FastAPI +: Pydantic for response validation, improved and 'free' error handling.
  - \+ FastAPI +: Faster setup.
  - \+ FastAPI +: Could setup with websockets to handle many concurrent events for a more production ready backend.
  - === Overall makes sense to use FastAPI as it hits the requirements of built in documentation and error handling out the box.
- Storage:
  - in-memory - no setup but offers no persistence of the data.
  - SQLite - very common/documented with FastAPI and persists data neatly. Does require some setup but not much, no Docker for example.
  - JSON - simple and persists but no querying, indexing, uniqueness checks.
  - Postgres in Docker. Most likely for a production setup but overkill for what this API needs to do.
  - SQLite seems like a sensible option of little setup, persistent data and no external services required. Also easy to switch to Postgres when production ready.
- Device History:
  - a status history table would be best to easily keep track of this.
  - device id, status and a timestamp.
  - example - can allow us to see how the temperature changed inside a home over the last day.
- Testing Framework:
  - Pytest is the obvious option here with TestClient.
  - test happy paths across the CRUD.
  - edge cases and error handling. Wrong or malformed ids, incorrect types, duplicate registration if possible, empty states with no errors.
- Device Ids - this should in fact be unique random ids like a uuid rather than incremental numbers so they aren't guessable.

## Setup

```bash
  # install dependencies
  pip install pytest httpx
  # to run the tests
  pytest -v
```

## Limitations / To Improve

- the schema
  - as more of a proof of concept I used status as a means of power, e.g. on/off.
  - in a real world scenario, if we had a thermometer as an example, this would not be just on/off, the current temperature would be a more useful piece of information.
