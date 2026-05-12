# CPU Thermal Throttle Investigation

Synthetic technician wiki page for lab demonstration only. This page does not contain proprietary procedures, internal URLs, customer data, or real company documentation.

## Symptoms

- CPU frequency remains below expected range under normal load.
- BMC thermal event log shows processor throttle warnings.
- Fans ramp after a heatsink or air-baffle service event.
- Operating system telemetry shows sustained thermal limiting.

## Checks

1. Confirm the air baffle is installed and seated.
2. Verify heatsink service notes match the affected CPU socket.
3. Compare inlet temperature against the synthetic lab environment range.
4. Review fan speed alerts before reseating thermal hardware.
5. Do not rerun workload validation until thermal events stop increasing.

## Related Pages

- wiki://fan-speed-alert

