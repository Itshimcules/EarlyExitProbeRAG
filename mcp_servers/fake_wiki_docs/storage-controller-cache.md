# Storage Controller Cache Status

Synthetic technician wiki page for lab demonstration only. This page does not contain proprietary procedures, internal URLs, customer data, or real company documentation.

## Purpose

Use this page when storage state looks stale after a drive service event or when firmware reports an unexpected cache protection warning.

## Checks

1. Capture the storage controller health summary before clearing cache status.
2. Confirm the battery or capacitor state is healthy in the synthetic lab inventory.
3. Check whether a recent NVMe reseat or RAID rebuild is still in progress.
4. Do not clear cache warnings while a rebuild is active.
5. Escalate if cache protection remains degraded after power and rebuild checks.

## Related Pages

- wiki://nvme-drive-missing
- wiki://raid-degraded-array

