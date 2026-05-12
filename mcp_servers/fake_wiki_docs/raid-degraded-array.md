# RAID Degraded Array Procedure

Synthetic technician wiki page for lab demonstration only. This page does not contain proprietary procedures, internal URLs, customer data, or real company documentation.

## Symptoms

- RAID status reports degraded after a drive replacement.
- One virtual disk remains online but not fully redundant.
- Rebuild progress is stalled or repeatedly restarts.
- Storage controller cache status changes during rebuild.

## Checks

1. Confirm the expected replacement drive is visible before starting rebuild actions.
2. Verify the array is degraded, not failed.
3. Record the virtual disk identifier and affected bay.
4. Let an active rebuild continue unless the progress counter is unchanged for the synthetic timeout window.
5. Review storage controller cache warnings before clearing or restarting a rebuild.

## Related Pages

- wiki://nvme-drive-missing
- wiki://storage-controller-cache

