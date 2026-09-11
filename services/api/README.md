# MyHub API

The production database baseline is PostgreSQL. SQLite is used only for fast local tests that do not depend on PostgreSQL locking semantics.

## Development

```bash
python -m pip install -e './services/api[test]'
pytest services/api/tests
```

Run migrations:

```bash
cd services/api
MYHUB_DATABASE_URL='postgresql+psycopg://myhub:myhub@localhost:5432/myhub' alembic upgrade head
```

Run API:

```bash
export MYHUB_DATABASE_URL='postgresql+psycopg://myhub:myhub@localhost:5432/myhub'
export MYHUB_BOOTSTRAP_TOKEN="$(python scripts/generate-bootstrap-token.py)"
uvicorn myhub.app.main:create_app --factory --reload
```

## Bootstrap

Fresh instances expose `UNINITIALIZED` at `GET /api/v1/instance`.

`POST /api/v1/bootstrap` performs one transaction:

```text
UNINITIALIZED -> BOOTSTRAPPING -> READY
```

The operator supplies `X-MyHub-Bootstrap-Token`; there is no token or Owner password shipped in source. The transaction creates one family, one user, exactly one initial Owner membership and Ed25519 instance identity material. READY instances reject first-time bootstrap.

The private identity key is never exposed by HTTP or logs. Encryption-at-rest and key rotation remain separate open security decisions rather than being silently invented inside SPEC-001.
