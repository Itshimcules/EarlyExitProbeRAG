# Synthetic Wiki Design

## Purpose

The synthetic wiki gives the harness realistic technician retrieval behavior without using real company documents, customer information, internal URLs, or proprietary SOPs.

Each page includes:

- a clear page title
- symptoms
- checks or procedure steps
- escalation notes
- explicit synthetic-data warning

## Current Pages

| Page ID | Title | Use Case |
| --- | --- | --- |
| `gpu-tray-reseat` | GPU Tray Reseat Procedure | Boot failure after GPU tray service |
| `psu-led-status` | PSU LED Status Reference | Power-state interpretation |
| `network-boot-failure` | Network Boot Failure Checklist | PXE and imaging failures |
| `bmc-reset-procedure` | BMC Reset Procedure | Stale management-controller state |
| `memory-training-failure` | Memory Training Failure Procedure | POST and DIMM training issues |
| `nvme-drive-missing` | NVMe Drive Missing Checklist | Missing storage devices after service |
| `storage-controller-cache` | Storage Controller Cache Status | Cache protection and stale storage state |
| `raid-degraded-array` | RAID Degraded Array Procedure | Rebuild and degraded-array triage |
| `fan-speed-alert` | Fan Speed Alert Triage | Fan tachometer and airflow alerts |
| `cpu-thermal-throttle` | CPU Thermal Throttle Investigation | Thermal limiting and fan-ramp symptoms |
| `firmware-update-rollback` | Firmware Update Rollback Plan | Controlled rollback after update symptoms |

## Style Rules

- Keep docs plausible but fake.
- Use generic lab language.
- Avoid real hardware serials, asset IDs, customer names, and URLs.
- Avoid copying proprietary procedure language.
- Prefer short troubleshooting pages that make retrieval behavior easy to inspect.
