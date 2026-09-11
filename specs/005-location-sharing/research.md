# Android Background Location Research — 2026-09-10

This is external implementation context. It does not override MyHub's consent-first specification.

## Expo Location / TaskManager

Current Expo documentation states that `expo-location` can subscribe to background location through TaskManager, subject to platform constraints.

Observed current documentation points:

- latest Expo docs list `expo-location` in SDK 57 and require appropriate foreground/background permissions;
- the background task must be defined at top-level scope with `TaskManager.defineTask`;
- on Android, foreground/background services are not available in Expo Go, so a development build is required for meaningful testing;
- on Android 11+, requesting background location opens system settings after the app should explain why the permission is needed;
- Android behavior when removing the app from recents varies by vendor;
- a terminated Android app is not automatically restarted by a location/geofence event through this Expo path.

Sources:
- https://docs.expo.dev/versions/latest/sdk/location/
- https://docs.expo.dev/versions/latest/sdk/task-manager/

## Android foreground-service location rules

Android's official guidance requires the `location` foreground-service type for applicable long-running location use and the `FOREGROUND_SERVICE_LOCATION` manifest permission on modern Android. Starting a location foreground service from background is constrained by while-in-use permissions unless background location authorization is available.

Source:
- https://developer.android.com/about/versions/14/changes/fgs-types-required

## Durable queue candidate

Expo SQLite provides a persistent SQLite database across app restarts and is a suitable candidate for an offline location queue. SQLCipher support exists through Expo configuration/development builds, but enabling it is a separate storage/security decision and is not silently mandated by this spec.

Source:
- https://docs.expo.dev/versions/latest/sdk/sqlite/

## MyHub implications

1. We cannot promise continuous tracking after Android terminates the process.
2. Freshness/staleness is therefore a product requirement, not cosmetic UI.
3. Expo Go is insufficient as the validation environment.
4. Vendor-specific behavior must be measured on real hardware.
5. Sampling intervals in the original handoff remain hypotheses until measurements exist.
6. Offline queue durability is technically feasible with the current Expo stack, but battery/restart behavior still needs empirical validation.
