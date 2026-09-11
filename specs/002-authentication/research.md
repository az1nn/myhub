# Authentication Research — 2026-09-10

This file records external implementation facts used by the plan. It does not override MyHub specs/ADRs.

## Python WebAuthn

Selected evaluation target: `webauthn` (Duo Labs), not the similarly named `py-webauthn` package.

At research time:

- package: `webauthn`;
- latest stable observed: 3.0.0, released 2026-06-29;
- Python requirement: >=3.10;
- PyPI classifies it Production/Stable.

Source: https://pypi.org/project/webauthn/

## Android Credential Manager and passkeys

Android's current guidance uses Credential Manager as the relying-party client API for passkey create/get flows. The client obtains options/challenge from the relying-party server, invokes Credential Manager, and returns the credential response for server verification.

Digital Asset Links are required for passkeys between native Android apps and the website/RP domain. For login credential sharing, Android documents relations including:

```text
delegate_permission/common.handle_all_urls
delegate_permission/common.get_login_creds
```

The `assetlinks.json` file is hosted by each website/instance domain under its well-known path and identifies Android package names plus SHA-256 signing certificate fingerprints.

Sources:
- https://developer.android.com/identity/credential-manager/prerequisites
- https://developer.android.com/identity/passkeys/create-passkeys

## MyHub-specific implication

Because MyHub distributes one Android app that connects to arbitrary family-owned self-hosted domains, each instance must be able to serve an association for the distributed MyHub Android package/signing certificate. This is why Digital Asset Links belongs to instance/bootstrap/auth configuration rather than a centralized MyHub SaaS.

The exact React Native/Expo bridge remains intentionally unselected until an empirical spike.

## Password hashing

OWASP currently recommends Argon2id for new password storage. One documented minimum profile is:

```text
memory = 19 MiB
iterations = 2
parallelism = 1
```

Equivalent profiles trade memory and iterations. MyHub should benchmark self-hosted target hardware and meet or exceed the accepted baseline.

Source: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

## Explicit non-research decisions

The following are MyHub architecture choices, not claims from these external sources:

- instance-owned authentication;
- opaque revocable Android sessions;
- one-time initial Owner enrollment bridge;
- no automatic recovery mechanism;
- backend authorization remains separate and authoritative.
