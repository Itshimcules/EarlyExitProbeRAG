# NVMe Drive Missing Checklist

Synthetic technician wiki page for lab demonstration only. This page does not contain proprietary procedures, internal URLs, customer data, or real company documentation.

## Symptoms

- One NVMe drive is missing from firmware inventory.
- A storage bay LED is dark after a drive service event.
- The operating system reports fewer block devices than expected.
- BMC storage inventory shows a bay present but not initialized.

## Checks

1. Confirm the missing bay number in firmware inventory before touching hardware.
2. Verify the drive carrier is fully latched and flush with the bay face.
3. Inspect the drive interposer for visible seating issues.
4. Reboot once only after confirming the bay LED and firmware inventory state.
5. If the drive remains missing, compare the symptom with storage controller cache status.

## Related Pages

- wiki://storage-controller-cache
- wiki://raid-degraded-array

