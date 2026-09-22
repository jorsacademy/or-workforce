# Synthetic Data Description

This project does not use external, proprietary, confidential, or real-company operational data.

The optimization instance is generated deterministically inside `staff_rostering.py`. The synthetic data include employee identifiers, hourly wage rates, skill qualifications, staffing requirements, shift definitions, and planned unavailability.

The data design is intended only to demonstrate the structure of a staff-rostering MILP model. It should not be interpreted as representative of any specific organization or industry benchmark.

## Data Components

- 18 fictional employees identified as `E01` through `E18`.
- Four technical skill categories: network, systems, security, and applications.
- Four eight-hour shifts covering a 24-hour operating cycle.
- A 14-day planning horizon.
- Deterministic skill qualifications generated from employee and skill indices.
- Deterministic day-shift-skill staffing requirements.
- A small set of synthetic unavailable employee-day combinations.

No personally identifiable information is included.
