# GPU Tray Reseat Procedure

Synthetic technician wiki page for lab demonstration only. This page does not contain proprietary procedures, internal URLs, customer data, or real company documentation.

## Symptoms

- Server does not complete POST after a GPU tray reseat.
- Fans ramp after power-on and remain high.
- BMC event log shows a PCIe slot presence change close to the service window.
- Front panel status LED may remain amber when GPU auxiliary power is not seated.

## First Checks

1. Power the system down using the approved lab workflow.
2. Confirm the GPU tray latch is fully closed and the tray sits flush against the chassis guide rails.
3. Verify each auxiliary GPU power lead is fully seated and follows the expected routing path.
4. Check PSU LEDs before replacing any GPU component.
5. Confirm no cable is pinched between the tray and chassis wall.

## Expected Result

After reseating, the tray should sit flush, PSU LEDs should show a healthy state, and the BMC event log should stop reporting new GPU presence changes.

## Escalation Notes

Escalate if the same slot reports presence changes after a second controlled reseat, or if PSU LED checks show a power fault. Do not replace the GPU tray based only on a single boot failure.

## Related Pages

- wiki://psu-led-status
- wiki://bmc-reset-procedure
