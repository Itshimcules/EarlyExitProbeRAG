# Network Boot Failure Checklist

Synthetic technician wiki page for lab demonstration only. This page does not contain proprietary procedures, internal URLs, customer data, or real company documentation.

## Symptoms

- Server reaches firmware prompt but does not PXE boot.
- NIC link LED is dark or flapping.
- Boot log reports no network boot target.
- Imaging workflow times out before the installer starts.

## Checks

1. Confirm the expected NIC port has physical link.
2. Verify the boot order includes the correct network target.
3. Check whether the system was moved to a staging VLAN without PXE service.
4. Confirm MAC address registration in the synthetic lab inventory.
5. Retry once after link state is stable for 60 seconds.

## Escalation Notes

Escalate to the lab network queue if multiple systems fail PXE boot on the same rack uplink. Escalate to platform support if only one NIC port fails after cable and VLAN checks.

