---
id: TASKSET-002-AUTHENTICATION
type: tasks
status: active
spec_id: SPEC-002-AUTHENTICATION
depends_on:
  - PLAN-002-AUTHENTICATION
task_metadata:
  TASK-002-01:
    priority: 1
    depends_on: []
  TASK-002-02:
    priority: 1
    depends_on: []
  TASK-002-03:
    priority: 2
    depends_on: [TASK-002-01, TASK-002-02]
  TASK-002-04:
    priority: 2
    depends_on: [TASK-002-01]
  TASK-002-05:
    priority: 2
    depends_on: [TASK-002-01]
  TASK-002-06:
    priority: 2
    depends_on: [TASK-002-01]
  TASK-002-07:
    priority: 3
    depends_on: [TASK-002-03]
  TASK-002-08:
    priority: 3
    depends_on: [TASK-002-03, TASK-002-04]
  TASK-002-09:
    priority: 3
    depends_on: [TASK-002-04, TASK-002-06]
  TASK-002-10:
    priority: 3
    depends_on: [TASK-002-01]
  TASK-002-11:
    priority: 4
    depends_on: [TASK-002-07, TASK-002-08, TASK-002-09]
  TASK-002-12:
    priority: 4
    depends_on: [TASK-002-05, TASK-002-09]
  TASK-002-13:
    priority: 4
    depends_on: [TASK-002-08, TASK-002-10]
  TASK-002-14:
    priority: 5
    depends_on: [TASK-002-11, TASK-002-12, TASK-002-13]
  TASK-002-15:
    priority: 5
    depends_on: [TASK-002-10]
  TASK-002-16:
    priority: 6
    depends_on: [TASK-002-14, TASK-002-15]
  TASK-002-17:
    priority: 7
    depends_on: [TASK-002-16]
---

# Tasks: Authentication

- [ ] TASK-002-01 Add authentication persistence model/migrations for passkeys, challenges, password credentials, sessions and initial Owner enrollment state.
- [ ] TASK-002-02 Implement the server WebAuthn provider behind an internal port, validating RP ID/origin/challenge/user verification.
- [ ] TASK-002-03 Implement short-lived single-use registration/authentication challenge service.
- [ ] TASK-002-04 Implement Argon2id password hashing plus normalized instance-local `login_name` rules.
- [ ] TASK-002-05 Implement opaque expiring/revocable server session service with hashed bearer secrets.
- [ ] TASK-002-06 Implement configurable Android Digital Asset Links document generation/endpoint.
- [ ] TASK-002-07 Implement initial Owner bootstrap-authorized passkey enrollment and permanent enrollment-gate closure.
- [ ] TASK-002-08 Implement normal passkey authentication options/verification flow.
- [ ] TASK-002-09 Implement password fallback enrollment/login flow without account-enumerating errors.
- [ ] TASK-002-10 Define and implement login abuse/throttling baseline without adding Redis.
- [ ] TASK-002-11 Add WebAuthn registration/authentication/replay/RP/origin/revocation tests.
- [ ] TASK-002-12 Add password/login-name/session expiry/revocation tests.
- [ ] TASK-002-13 Add initial Owner enrollment, concurrency and post-enrollment bootstrap-token rejection tests.
- [ ] TASK-002-14 Publish detailed HTTP/OpenAPI authentication contracts and operator documentation.
- [ ] TASK-002-15 Execute the real-device Android Credential Manager + Expo development-build spike and record results.
- [ ] TASK-002-16 Sync Requirement/Spec/Task/Code/Test relationships into the Engineering Graph and run drift/impact checks.
- [ ] TASK-002-17 Add final graph validation evidence to the implementing PR.

## Initial task DAG

```text
Wave 1
├── TASK-002-01 persistence
└── TASK-002-02 WebAuthn provider

Wave 2
├── TASK-002-03 challenges
├── TASK-002-04 password hashing/login name
├── TASK-002-05 sessions
└── TASK-002-06 Digital Asset Links

Wave 3
├── TASK-002-07 initial Owner enrollment
├── TASK-002-08 passkey authentication
├── TASK-002-09 password fallback
└── TASK-002-10 abuse controls

Wave 4
├── TASK-002-11 WebAuthn tests
├── TASK-002-12 password/session tests
├── TASK-002-13 Owner enrollment tests
└── TASK-002-15 Android passkey spike

Wave 5
└── TASK-002-14 contracts/docs

Wave 6
└── TASK-002-16 graph sync/analysis

Wave 7
└── TASK-002-17 graph validation evidence
```

`task_metadata` is canonical for machine-readable dependencies. The wave projection is for humans and must be recalculated by the Engineering Graph before parallel execution.
