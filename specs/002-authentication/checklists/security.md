# Authentication Security Checklist

## WebAuthn / passkeys

- [ ] Registration and authentication challenges are cryptographically random.
- [ ] Challenges expire and are accepted once only.
- [ ] Expected RP ID is explicit and validated.
- [ ] Accepted origins are explicit and validated.
- [ ] User verification policy is explicit.
- [ ] Unknown and revoked credentials fail closed.
- [ ] Private passkey material is never sent to/stored by MyHub.
- [ ] Replay tests exist.
- [ ] Canonical host/RP ID cannot be casually changed after credential enrollment.

## Initial Owner enrollment

- [ ] Bootstrap token authorizes credential enrollment only, never a general session.
- [ ] Enrollment target is the exact initial Owner from SPEC-001.
- [ ] Enrollment path closes permanently after first successful Owner credential setup.
- [ ] Concurrent enrollment cannot establish multiple bootstrap-authorized owner identities.
- [ ] Bootstrap token is never logged or persisted by request handling.

## Password fallback

- [ ] Password storage uses Argon2id.
- [ ] Work factor meets/exceeds the accepted OWASP baseline and is configurable.
- [ ] `display_name` is not used as authentication identity.
- [ ] `login_name` uniqueness/normalization is deterministic.
- [ ] Authentication errors avoid useful account-enumeration differences.
- [ ] Password plaintext never reaches logs/telemetry.

## Sessions

- [ ] Bearer secret has high cryptographic entropy.
- [ ] Server persists only a verifier/hash of the bearer secret.
- [ ] Sessions expire.
- [ ] Sessions are revocable server-side.
- [ ] Revoked/expired sessions fail closed.
- [ ] Android stores session material in platform-secure storage.
- [ ] Web cookie/CSRF behavior is not accidentally implied by the Android session design.

## Self-hosted Android association

- [ ] Instance can serve `/.well-known/assetlinks.json`.
- [ ] Package name is configured rather than hard-coded into domain logic.
- [ ] Release signing SHA-256 fingerprint is supported.
- [ ] Debug/development build association is tested separately.
- [ ] Credential Manager failure and unverified association are visible to the user.

## Recovery boundary

- [ ] No security questions.
- [ ] No hidden master password.
- [ ] No permanent bootstrap bypass.
- [ ] No mandatory email/Google dependency introduced implicitly.
- [ ] Lost-all-credentials case fails closed pending the dedicated recovery decision.
