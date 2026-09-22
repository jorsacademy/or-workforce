# A Hybrid Personnel Scheduling Model for Staff Rostering Problems

This repository presents a synthetic mixed-integer linear programming (MILP) model for personnel scheduling and staff rostering.

The scenario is intentionally fictional and uses fully synthetic data. It does not represent, reproduce, or derive from the operational data of any real company, public institution, airline, hospital, or other organization.

## Scenario

The model represents a regional technical support operations center that must provide continuous coverage across several technical competencies. Employees may hold multiple qualifications and must be assigned to shifts while satisfying labor, availability, coverage, and rest constraints.

The planning horizon is 14 days. Four shift types are available:

- `EARLY`: 06:00-14:00
- `DAY`: 09:00-17:00
- `LATE`: 14:00-22:00
- `NIGHT`: 22:00-06:00

The model covers four synthetic skill categories:

- Network support
- Systems operations
- Security operations
- Application support

## Optimization Model

The principal binary decision variable is:

`x[i,d,w] = 1` if employee `i` is assigned to shift `w` on day `d`, and `0` otherwise.

A second binary variable links qualified employees to skill coverage:

`y[i,d,w,s] = 1` if employee `i` covers skill `s` while assigned to shift `w` on day `d`.

The objective minimizes total labor cost together with a workload-balancing penalty.

The model includes the following constraints:

1. Skill-specific staffing demand must be covered for every day and shift.
2. Employees may provide only skills for which they are qualified.
3. An employee can cover at most one skill role within an assigned shift.
4. Each employee can work at most one shift per day.
5. Predefined unavailable days cannot receive assignments.
6. Employees cannot exceed the maximum number of consecutive workdays.
7. Working hours are limited in every rolling seven-day window.
8. Incompatible late-to-early and night-to-morning transitions are prohibited.
9. Total workdays are capped over the planning horizon.
10. A fairness term penalizes deviations from a target workload.

## Reproducibility

All data in `staff_rostering.py` are deterministic. No external datasets or proprietary inputs are required.

The current synthetic instance contains:

- 18 employees
- 14 planning days
- 4 shifts
- 4 skill categories
- employee-specific hourly wage rates
- multi-skill qualification assignments
- day-shift-skill demand values
- planned unavailability

## Installation

Python 3.10 or later is recommended.

```bash
pip install -r requirements.txt
```

## Usage

```bash
python staff_rostering.py
```

The script solves the model with PuLP's CBC interface and prints the solver status, objective value, day-by-day shift assignments, and the skill role covered by each assigned employee.

## Project Structure

```text
.
├── README.md
├── LICENSE.md
├── requirements.txt
├── staff_rostering.py
├── data/
│   └── README.md
└── .gitignore
```

## Academic and Educational Scope

This repository is intended for educational, academic, and non-commercial research use. The model is a compact teaching implementation rather than a production workforce-management system. Real deployments would normally require additional features such as contractual rules, employee preferences, overtime tiers, leave categories, demand uncertainty, shift bids, seniority, regulatory calendars, and audit controls.

## License

This project is distributed under a custom non-commercial license. Commercial use is not permitted. See `LICENSE.md` for the complete terms.
