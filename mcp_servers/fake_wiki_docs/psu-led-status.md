# PSU LED Status Reference

Synthetic technician wiki page for lab demonstration only. This page does not contain proprietary procedures, internal URLs, customer data, or real company documentation.

## Purpose

Use PSU LED state to distinguish upstream power, power-supply, and downstream load symptoms before replacing field hardware.

## LED Meanings

- Solid green: input and output are healthy.
- Blinking green: PSU is present but in standby.
- Amber: PSU fault or downstream load issue.
- No LED: check AC input, power cable, and outlet path.

## Troubleshooting Flow

1. Compare both PSU modules before moving hardware.
2. Swap the AC input cable only if the LED is off.
3. If one PSU is amber and the other is green, record the module bay and BMC power event.
4. If both PSUs are amber after a GPU tray reseat, inspect GPU auxiliary power and tray seating.
5. Do not clear BMC logs until after the service notes are captured.

## Related Pages

- wiki://gpu-tray-reseat
- wiki://bmc-reset-procedure

