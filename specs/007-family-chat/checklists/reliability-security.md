# Family Chat Reliability & Security Checklist

- [ ] One canonical family channel is tenant-scoped.
- [ ] Read/send check active Membership and capabilities server-side.
- [ ] Sender user/tenant identity is server-derived.
- [ ] Client assigns stable `client_message_id` before first send.
- [ ] Response loss + retry cannot duplicate message.
- [ ] Same idempotency key with different content is rejected.
- [ ] HTTP cursor ordering is deterministic.
- [ ] WebSocket is not the only recovery source.
- [ ] Reconnect fetches missed messages.
- [ ] Pending local message is visually distinct from persisted message.
- [ ] Push failure cannot roll back chat persistence.
- [ ] Membership removal stops future authorized realtime/message reads.
- [ ] Message body is absent from normal logs/telemetry.
- [ ] Oversized text is rejected; attachments/base64 are not smuggled through V0.1 text API.
- [ ] No E2EE claim is made before an actual E2EE design exists.
- [ ] Retention remains explicitly unresolved rather than silently infinite.
