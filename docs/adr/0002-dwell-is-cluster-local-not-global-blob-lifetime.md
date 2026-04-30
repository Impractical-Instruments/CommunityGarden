# Dwell is tracked per-cluster, not exported from BlobStabilizer

`FlowerCluster` maintains its own `_blob_dwell` counter for each Blob Track within its `influence_radius_cm`. This is intentionally separate from `BlobStabilizer`'s internal `seen_frames` counter.

The two measure different things:

- **`seen_frames`** (BlobStabilizer) — how many frames a Blob Track has existed anywhere in the world.
- **`_blob_dwell`** (FlowerCluster) — how many consecutive frames a Blob Track has been within *this cluster's* influence radius.

The Attraction formula uses cluster-local dwell to prefer Visitors who are lingering *near this flower*, not Visitors who have merely been somewhere in the space for a long time. If a Visitor walks from one cluster to another, `seen_frames` keeps climbing but `_blob_dwell` correctly resets for the new cluster.

## Consequences

Do not move dwell tracking into `BlobStabilizer` or expose `seen_frames` via `TrackedBlob` as a substitute for dwell. Doing so would silently change the semantics of the Attraction policy.
