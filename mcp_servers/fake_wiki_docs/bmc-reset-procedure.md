# BMC Reset Procedure

Synthetic technician wiki page for lab demonstration only. This page does not contain proprietary procedures, internal URLs, customer data, or real company documentation.

## When To Use

Use a BMC reset when the management controller is responsive enough to accept commands but sensor data, event entries, or remote console state appears stale.

## Procedure

1. Capture current BMC event entries before clearing or resetting anything.
2. Confirm the host workload can tolerate a management-controller reset.
3. Issue the approved synthetic lab reset command from the management network.
4. Wait for the BMC web endpoint or API endpoint to return healthy status.
5. Compare sensor readings after reset against the pre-reset service notes.

## Do Not Use

Do not use a BMC reset to hide repeated hardware errors. If PSU, GPU, or memory faults recur after reset, continue with the relevant hardware troubleshooting page.

