---
id: TASKSET-007-FAMILY-CHAT
type: tasks
status: active
spec_id: SPEC-007-FAMILY-CHAT
depends_on:
  - PLAN-007-FAMILY-CHAT
task_metadata:
  TASK-007-01:
    priority: 1
    depends_on: []
  TASK-007-02:
    priority: 1
    depends_on: []
  TASK-007-03:
    priority: 2
    depends_on: [TASK-007-01, TASK-007-02]
  TASK-007-04:
    priority: 2
    depends_on: [TASK-007-01]
  TASK-007-05:
    priority: 3
    depends_on: [TASK-007-03, TASK-007-04]
  TASK-007-06:
    priority: 3
    depends_on: [TASK-007-03]
  TASK-007-07:
    priority: 3
    depends_on: [TASK-007-05]
  TASK-007-08:
    priority: 4
    depends_on: [TASK-007-05, TASK-007-06, TASK-007-07]
  TASK-007-09:
    priority: 5
    depends_on: [TASK-007-08]
  TASK-007-10:
    priority: 6
    depends_on: [TASK-007-09]
---

# Tasks: Family Chat

- [ ] TASK-007-01 Add one-family-channel + Message persistence/migration and stable cursor ordering.
- [ ] TASK-007-02 Implement tenant/member message authorization policy.
- [ ] TASK-007-03 Implement idempotent message creation keyed by sender + `client_message_id`.
- [ ] TASK-007-04 Implement cursor-based HTTP history endpoint.
- [ ] TASK-007-05 Implement versioned `message.created` realtime publication after commit and authorized subscription.
- [ ] TASK-007-06 Implement mobile pending/sent/failed send queue and retry reconciliation.
- [ ] TASK-007-07 Integrate post-commit generic notification intent boundary for SPEC-008.
- [ ] TASK-007-08 Add authorization/idempotency/pagination/realtime-failure/reconnect/mobile-state tests.
- [ ] TASK-007-09 Publish chat API/realtime contracts, retention open-decision note and update graph metadata.
- [ ] TASK-007-10 Add Engineering Graph validation evidence to the implementing PR.

## Initial waves

```text
Wave 1
├── TASK-007-01 persistence
└── TASK-007-02 policy

Wave 2
├── TASK-007-03 idempotent send
└── TASK-007-04 history

Wave 3
├── TASK-007-05 realtime
└── TASK-007-06 mobile send state

Wave 4
└── TASK-007-07 notification intent

Wave 5
└── TASK-007-08 tests

Wave 6
└── TASK-007-09 contracts + graph

Wave 7
└── TASK-007-10 evidence
```
