---
id: DOC-DATA-001
type: data-model
status: active
constrained_by:
  - ADR-002
  - ADR-013
  - ADR-014
  - ADR-015
---

# MyHub Data Model Baseline

This is a logical baseline, not the final migration schema.

## Tenant

```text
id uuid PK
name
created_at
updated_at
settings jsonb
```

## User

```text
id uuid PK
display_name
created_at
updated_at
```

## Membership

```text
id uuid PK
tenant_id uuid FK
user_id uuid FK
role
status
created_at
updated_at
UNIQUE(tenant_id, user_id)
```

## Device

```text
id uuid PK
tenant_id uuid FK
user_id uuid FK
name
platform
location_source boolean
registered_at
last_seen_at
revoked_at nullable
```

Invariant: one active location source per user/tenant unless superseded by a future ADR.

## Invitation

```text
id uuid PK
tenant_id uuid FK
created_by_user_id uuid FK
token_hash
expires_at
max_uses
use_count
revoked_at nullable
created_at
```

## LocationEvent

```text
id uuid PK
tenant_id uuid FK
user_id uuid FK
device_id uuid FK
latitude
longitude
accuracy_m nullable
altitude_m nullable
speed_mps nullable
heading_deg nullable
battery_pct nullable
source
captured_at
received_at
```

`captured_at` is client capture time. `received_at` is server receipt time.

## CurrentLocation

```text
tenant_id uuid
user_id uuid
device_id uuid
location_event_id uuid
latitude
longitude
accuracy_m nullable
battery_pct nullable
captured_at
received_at
freshness_state
PRIMARY KEY (tenant_id, user_id)
```

This is a read model/projection.

## Channel

```text
id uuid PK
tenant_id uuid FK
kind
name nullable
created_at
```

V0.1 starts with one family channel.

## Message

```text
id uuid PK
tenant_id uuid FK
channel_id uuid FK
user_id uuid FK
content text
reply_to_message_id uuid nullable
created_at
edited_at nullable
deleted_at nullable
```

## Place

```text
id uuid PK
tenant_id uuid FK
name
latitude
longitude
radius_m
settings jsonb
created_at
updated_at
```

## Reminder

```text
id uuid PK
tenant_id uuid FK
created_by_user_id uuid FK
target_user_id uuid FK
message
trigger_type
trigger_at nullable
place_id uuid nullable
event_type nullable
status
created_at
completed_at nullable
```

## Tenant-scoping rule

Relevant business queries MUST scope by authenticated membership tenant. A supplied `tenant_id` is never sufficient authorization by itself.

## Location ingestion

`LocationEvent.id` SHOULD be generated on the client before queuing. Repeated delivery of the same event ID MUST be idempotent.

## Retention

Location-history retention remains configurable and unresolved. `CurrentLocation` is a projection, not a substitute for the retention-controlled history model.

## Candidate indexes

```text
membership(tenant_id, user_id)
device(tenant_id, user_id)
device(tenant_id, user_id, location_source)
location_event(tenant_id, user_id, captured_at DESC)
location_event(device_id, captured_at DESC)
current_location(tenant_id, user_id)
message(tenant_id, channel_id, created_at DESC)
place(tenant_id)
invitation(tenant_id, expires_at)
```

Exact indexes require measurement against concrete schema/query plans.
