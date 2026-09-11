# Device Registration Security & Privacy Checklist

- [ ] Device ownership is derived from authenticated/onboarding authority, not client IDs.
- [ ] No IMEI, serial number or advertising ID is required.
- [ ] Raw device credential is disclosed once only.
- [ ] Server stores only device secret verifier/hash.
- [ ] Mobile stores raw device credential using platform-protected secure storage.
- [ ] Device token never appears in logs.
- [ ] Device credential is scoped; it is not a general user session.
- [ ] Revocation immediately blocks device-authenticated operations.
- [ ] At most one non-revoked location source exists per user.
- [ ] Source switching is atomic.
- [ ] Source switching cannot activate location sharing.
- [ ] Revoking current source does not silently promote another source.
- [ ] Administrative revoke permission cannot silently activate another person's tracking.
- [ ] Tenant isolation tests exist.
- [ ] Reinstallation/lost local credential is treated as a new device unless secure continuity is proven.
