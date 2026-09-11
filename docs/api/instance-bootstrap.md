---
id: API-SPEC-001-BOOTSTRAP
type: api-contract
status: active
requires:
  - REQ-BOOT-001
  - REQ-BOOT-002
  - REQ-BOOT-003
  - REQ-BOOT-004
constrained_by:
  - ADR-010
  - ADR-018
---

# Instance Bootstrap API Contract

## GET `/api/v1/instance`

Unauthenticated discovery endpoint. Before bootstrap it returns lifecycle state. After READY it exposes only non-secret instance identity needed by clients.

## POST `/api/v1/bootstrap`

Header:

```text
X-MyHub-Bootstrap-Token: <operator-controlled secret>
```

Body:

```json
{
  "family_name": "Silva Family",
  "canonical_url": "https://family.example.com",
  "owner_display_name": "Alan"
}
```

Success is `201 Created` with `state=READY`, public instance identity and created IDs.

Stable bootstrap errors:

```text
BOOTSTRAP_UNAUTHORIZED         401
INSTANCE_ALREADY_INITIALIZED  409
BOOTSTRAP_IN_PROGRESS         409
```

All structured bootstrap errors carry `request_id`.

## Security

- No shipped/default Owner credential.
- Bootstrap token comes from runtime configuration and is compared in constant time.
- Token and private identity key are never returned by APIs or logged.
- Public non-local canonical URLs require HTTPS.
- First bootstrap is transactionally serialized by the singleton bootstrap row lock in PostgreSQL.
