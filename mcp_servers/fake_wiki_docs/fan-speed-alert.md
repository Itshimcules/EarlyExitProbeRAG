# Fan Speed Alert Triage

Synthetic technician wiki page for lab demonstration only. This page does not contain proprietary procedures, internal URLs, customer data, or real company documentation.

## Symptoms

- Fans remain at high speed after boot.
- BMC reports a fan speed threshold warning.
- A fan module is present but not reporting tachometer data.
- Thermal alerts appear after a chassis service event.

## Checks

1. Confirm all fan modules are fully seated.
2. Compare fan tachometer readings before swapping modules.
3. Inspect for a loose air baffle or blocked airflow path.
4. Check CPU thermal throttle events before replacing a fan module.
5. Escalate if two adjacent fans report zero tachometer readings.

## Related Pages

- wiki://cpu-thermal-throttle

