# Family Map Privacy & Truthfulness Checklist

- [ ] Every coordinate marker has freshness/status semantics.
- [ ] `captured_at` drives displayed age.
- [ ] Delayed event cannot render as “updated now”.
- [ ] Approximate/coarse samples are distinguishable.
- [ ] PAUSED is visible and never implied live.
- [ ] Opening map does not activate viewer sharing/GPS.
- [ ] Backend, not client, filters authorized location visibility.
- [ ] WebSocket reconnect re-fetches snapshot.
- [ ] Older realtime events cannot regress a newer marker.
- [ ] Tile-provider privacy implications are documented.
- [ ] Production does not use MapLibre demo tiles.
- [ ] No mandatory MyHub-author-operated map service exists.
- [ ] Tile failure keeps textual member/location status available.
- [ ] Coordinate cache preserves original timestamps and is cleared on logout/instance switch.
