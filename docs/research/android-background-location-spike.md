---
id: SPIKE-ANDROID-LOCATION-001
type: research
status: planned
---

# Android Background Location Spike

## Goal

Empirically validate whether React Native + Expo can provide reliable, privacy-compliant background location for MyHub on Android with acceptable battery impact.

No final production sampling policy is accepted before this spike.

## Scenarios

Test foreground, background, screen locked, process terminated, reboot, Doze mode, battery optimization enabled/disabled, temporary and long network loss, recovery, local queue growth/sync, GPS unavailable, approximate permission, precise permission, background permission, permission revocation, app upgrade and representative manufacturers.

## Measurements

For every scenario record:

```text
device/model
Android version
permission state
battery optimization state
requested interval
achieved interval
accuracy distribution
capture count
upload delay
queue depth
recovery time
battery delta
process kill/restart behavior
reboot recovery behavior
unexpected OS restrictions
```

## Sampling hypothesis

Starting hypothesis only:

```text
stationary        ~5-10 min
walking           ~1-2 min
fast/vehicle      ~20-60 sec
active map follow temporarily higher
```

Evidence may reject these values.

## Required invariants

- Paused sharing never becomes active due to worker/reboot.
- Revoked permission stops capture.
- Approximate permission is represented honestly.
- Queued events retain original `captured_at`.
- Late sync does not present old coordinates as current.
- Duplicate retries do not duplicate server events.
- Process restart does not silently lose durable queued events.
- Explicit sharing state survives lifecycle events safely.

## Exit criteria

The spike produces: recommended Android collection strategy; measured battery profile; known manufacturer/OS limitations; confirmed offline queue behavior; recommendation on Expo-managed versus native/custom-development needs if limitations appear; production-candidate freshness thresholds; and explicit unresolved risks.

Architecture-changing conclusions MUST update affected specs/ADRs and run Engineering Graph impact analysis before implementation continues.
