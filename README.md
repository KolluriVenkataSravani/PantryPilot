# Pantry Pilot

A small pantry inventory app to track quantities and best-before dates, find food that needs using soon, and cut down on food waste. It includes a browser UI, a JSON API, and PostgreSQL. Built as a hands-on project for learning Docker, Compose, and GitHub Actions.

## Run it with Docker Compose

1. Copy `.env.example` to `.env`. The sample password is for local learning only; change it if this app will be reachable by anyone else.
2. From this folder, run:

   ```sh
   docker compose up --build
   ```

3. Open <http://localhost:8000>. The interactive API docs are at <http://localhost:8000/docs>.

Compose starts the app and PostgreSQL. The app waits for the database health check before starting; Compose's internal DNS lets the app connect to the database using the service name `db`. PostgreSQL data is kept in the named `pantry_data` volume, so it survives container replacement.

### Useful Docker commands

```sh
docker compose ps                         # See service and health status
docker compose logs -f app                # Follow application logs
docker compose exec db psql -U pantry -d pantry  # Open a database shell
docker compose down                       # Stop and remove containers; keep database data
docker compose down --volumes              # Also delete the database volume and its data
```

The last command permanently removes the saved pantry data.

## Run locally without Docker

Use Python 3.10 or newer. Start a PostgreSQL database and set `DATABASE_URL`, or use the default local SQLite database:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit <http://localhost:8000>. With SQLite, data is stored in `pantry.db`.

## Tests

The API tests use an isolated in-memory SQLite database, so they do not need a running PostgreSQL server:

```sh
pytest -q
```

## GitHub Actions pipeline

`.github/workflows/ci.yml` runs for pushes and pull requests. It checks out the source, installs Python dependencies, runs the test suite, then builds the Docker image. To try the same steps locally:

```sh
pip install -r requirements.txt
pytest -q
docker build -t pantry-pilot:local .
```

## Project map

```text
app/
  config.py       Environment configuration
  database.py     SQLAlchemy engine and session dependency
  models.py       Database table definitions
  schemas.py      API request/response validation
  repository.py   Database queries and persistence
  routes.py       HTTP endpoints
  main.py         FastAPI app setup and static UI
  static/         Browser interface
tests/            API tests with a separate test database
Dockerfile        Reproducible, non-root application image
compose.yaml      App + PostgreSQL services and persistent volume
.github/workflows/ci.yml
```

## API at a glance

- `GET /api/items?q=oats&status=expiring` — list, search, and filter items (`expired`, `expiring`, or `fresh`)
- `POST /api/items` — add an item (JSON fields: `name`, `quantity`, `unit`, `category`, `expires_on`, `notes`)
- `PUT /api/items/{id}` — update an item using the same JSON fields
- `DELETE /api/items/{id}` — remove an item
- `GET /api/summary` — pantry counts
- `GET /api/health` — application and database readiness check
