---
id: TASKSET-008-PUSH-NOTIFICATIONS
type: tasks
status: active
spec_id: SPEC-008-PUSH-NOTIFICATIONS
depends_on:
  - PLAN-008-PUSH-NOTIFICATIONS
task_metadata:
  TASK-008-01:
    priority: 1
    depends_on: []
    implemented_by:
      - services/api/src/myhub/modules/notifications/domain.py
      - services/api/src/myhub/modules/notifications/provider.py
    validated_by:
      - services/api/tests/unit/notifications/test_domain.py
  TASK-008-02:
    priority: 1
    depends_on: []
    implemented_by:
      - services/api/src/myhub/modules/notifications/models.py
      - services/api/migrations/versions/*_push_notifications.py
    validated_by:
      - services/api/tests/integration/notifications/test_persistence.py
  TASK-008-03:
    priority: 2
    depends_on: [TASK-008-01, TASK-008-02]
    implemented_by:
      - services/api/src/myhub/modules/notifications/routes.py
      - services/api/src/myhub/modules/notifications/service.py
    validated_by:
      - services/api/tests/integration/notifications/test_registration_api.py
  TASK-008-04:
    priority: 2
    depends_on: [TASK-008-01, TASK-008-02]
    implemented_by:
      - services/api/src/myhub/modules/notifications/outbox.py
    validated_by:
      - services/api/tests/integration/notifications/test_outbox.py
  TASK-008-05:
    priority: 2
    depends_on: [TASK-008-01]
    implemented_by:
      - services/api/src/myhub/modules/notifications/fcm.py
    validated_by:
      - services/api/tests/unit/notifications/test_fcm_provider.py
  TASK-008-06:
    priority: 3
    depends_on: [TASK-008-04, TASK-008-05]
    implemented_by:
      - services/api/src/myhub/modules/notifications/worker.py
    validated_by:
      - services/api/tests/integration/notifications/test_worker.py
  TASK-008-07:
    priority: 3
    depends_on: [TASK-008-03, TASK-008-04]
    implemented_by:
      - services/api/src/myhub/modules/chat/service.py
    validated_by:
      - services/api/tests/integration/notifications/test_chat_notification_intent.py
  TASK-008-08:
    priority: 3
    depends_on: [TASK-008-03]
    implemented_by:
      - apps/mobile/src/features/notifications/register-device-token.ts
    validated_by:
      - apps/mobile/src/features/notifications/__tests__/register-device-token.test.ts
  TASK-008-09:
    priority: 4
    depends_on: [TASK-008-08]
    implemented_by:
      - apps/mobile/src/features/notifications/notification-response.ts
    validated_by:
      - apps/mobile/src/features/notifications/__tests__/notification-response.test.ts
  TASK-008-10:
    priority: 4
    depends_on: [TASK-008-06, TASK-008-07]
    implemented_by:
      - services/api/src/myhub/modules/notifications/metrics.py
    validated_by:
      - services/api/tests/integration/notifications/test_observability.py
  TASK-008-11:
    priority: 5
    depends_on: [TASK-008-06, TASK-008-08, TASK-008-09]
    validated_by:
      - docs/research/android-push-notification-spike.md
  TASK-008-12:
    priority: 6
    depends_on: [TASK-008-03, TASK-008-05, TASK-008-06, TASK-008-07, TASK-008-10, TASK-008-11]
    validated_by:
      - services/api/tests/integration/notifications/test_push_end_to_end.py
  TASK-008-13:
    priority: 7
    depends_on: [TASK-008-12]
  TASK-008-14:
    priority: 8
    depends_on: [TASK-008-13]
---

# Tasks: Push Notifications

- [ ] TASK-008-01 Define provider-neutral notification domain and `PushProvider` port.
- [ ] TASK-008-02 Add push-registration, notification-outbox and preference persistence/migrations.
- [ ] TASK-008-03 Implement authorized Device push-registration/update/removal API.
- [ ] TASK-008-04 Implement transactional notification outbox and idempotent intent creation.
- [ ] TASK-008-05 Implement FCM HTTP v1 provider adapter and error classification.
- [ ] TASK-008-06 Implement concurrency-safe worker claim/retry/terminal-failure processing.
- [ ] TASK-008-07 Integrate committed family-chat messages with recipient notification intents.
- [ ] TASK-008-08 Implement Android native FCM token registration + token-rotation listener.
- [ ] TASK-008-09 Implement Android notification response/cold-start navigation reconciliation.
- [ ] TASK-008-10 Add push health/metrics/logging without secret leakage.
- [ ] TASK-008-11 Run and document real-device Android push validation.
- [ ] TASK-008-12 Add backend/provider/mobile integration coverage for the complete V0.1 flow.
- [ ] TASK-008-13 Sync Requirement/Spec/Task/Code/Test relationships into Engineering Graph.
- [ ] TASK-008-14 Attach graph validation/impact evidence to the implementing PR.

## Initial graph projection

```text
Wave 1
├── TASK-008-01
└── TASK-008-02

Wave 2
├── TASK-008-03
├── TASK-008-04
└── TASK-008-05

Wave 3
├── TASK-008-06
├── TASK-008-07
└── TASK-008-08

Wave 4
├── TASK-008-09
└── TASK-008-10

Wave 5
└── TASK-008-11

Wave 6
└── TASK-008-12

Wave 7
└── TASK-008-13

Wave 8
└── TASK-008-14
```

`task_metadata` is canonical for machine-readable scheduling. The wave diagram is only a human-readable projection and MUST be recalculated by Engineering Graph before parallel implementation.
