# Family Membership & Invitation Security Checklist

## Invitation bearer secret

- [ ] Token uses cryptographically secure random material.
- [ ] Persisted record contains only token verifier/hash.
- [ ] Secret comparison is constant-time.
- [ ] Raw token is absent from application/access/audit logs.
- [ ] Expiration is mandatory.
- [ ] Revocation is supported.
- [ ] Consumption is one-use and atomic.
- [ ] Concurrent acceptance cannot create two memberships.

## Tenant and authorization

- [ ] Invitation creation checks `members.invite` server-side.
- [ ] Membership removal checks `members.remove` server-side.
- [ ] Membership queries are tenant-scoped.
- [ ] Normal invites cannot assign Owner.
- [ ] Last Owner cannot be removed by normal membership removal.
- [ ] Removed/suspended membership fails protected-resource authorization even if a session token remains otherwise valid.

## Onboarding

- [ ] Invitation grants onboarding authority only.
- [ ] Invitation token alone cannot access map/chat/location/member list.
- [ ] Credential enrollment is verified before a normal session is established.
- [ ] Failed credential enrollment does not leave an active orphan membership.
- [ ] Preview exposes only minimal family/instance metadata.
- [ ] Joining does not activate location sharing or OS location permissions.

## Link/QR handling

- [ ] Payload contains only server locator + invitation material required for onboarding.
- [ ] Token placement is reviewed for browser history/referrer/access-log leakage.
- [ ] Deep-link/App Link behavior is tested on Android.
- [ ] Server/instance identity handling follows the approved server-identity design when that design is finalized.
