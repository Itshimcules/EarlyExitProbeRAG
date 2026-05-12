# Firmware Update Rollback Plan

Synthetic technician wiki page for lab demonstration only. This page does not contain proprietary procedures, internal URLs, customer data, or real company documentation.

## When To Use

Use this page when a synthetic firmware update causes boot, inventory, or management-controller symptoms that were not present before the update window.

## Checks

1. Record current firmware versions before starting rollback.
2. Confirm the rollback target is approved for the synthetic lab platform.
3. Capture BMC and storage controller health summaries.
4. Roll back one firmware component at a time.
5. Re-run only the affected validation checks after each rollback step.

## Related Pages

- wiki://bmc-reset-procedure
- wiki://network-boot-failure

