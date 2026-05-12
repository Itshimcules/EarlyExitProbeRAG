# Memory Training Failure Procedure

Synthetic technician wiki page for lab demonstration only. This page does not contain proprietary procedures, internal URLs, customer data, or real company documentation.

## Symptoms

- Boot pauses during memory initialization.
- POST code remains in a memory training range.
- BMC event log shows a DIMM training or initialization warning.
- System boots after removing recently added memory.

## Checks

1. Confirm the DIMM population follows the platform memory map.
2. Inspect recently serviced DIMM slots for uneven latch closure.
3. Reseat only the DIMM associated with the newest event entry.
4. Run one controlled boot after reseat before changing additional variables.
5. Record slot, capacity, and synthetic serial placeholder in the service note.

## Escalation Notes

Escalate if the same DIMM slot fails training after a known-good module is tested, or if multiple channels fail at the same time after a firmware update.

