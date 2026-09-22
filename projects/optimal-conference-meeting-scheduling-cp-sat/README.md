# Optimal Conference Meeting Scheduling with CP-SAT

This repository contains a complete educational Operations Research case study for scheduling a multi-day academic conference with Google OR-Tools CP-SAT.

The project is designed as an advanced optimization example suitable for graduate or PhD-level study. It integrates session placement, room assignment, multi-slot durations, room equipment compatibility, speaker availability, participant availability, preference satisfaction, session capacities, and soft penalties for related-session conflicts.

The synthetic conference contains 150 participants, 50 sessions, 40 speakers, 10 heterogeneous venues, 3 conference days, 5 timeslots per day, session durations of one or two timeslots, five thematic tracks, participant preference rankings, participant and speaker availability, room capacity and equipment requirements, and soft penalties for overlapping related sessions.

All data are generated deterministically from a fixed random seed so that the same instance can be reproduced.

## Decision Variables

The model uses three principal binary variable families.

- `x[s,t,v] = 1` if session `s` starts at timeslot `t` in venue `v`.
- `y[p,s] = 1` if participant `p` attends preferred session `s`.
- `z[p,s,t,v] = 1` if participant `p` attends session `s` when that session is placed at timeslot `t` in venue `v`.

The `z` variables provide a valid linearization between participant attendance and the selected session placement.

## Objective

The model maximizes weighted participant preference satisfaction and penalizes overlaps between related sessions.

For participant `p` and preferred session `s`, let `w[p,s]` denote the rank-dependent preference weight. The primary term is

```text
maximize sum(w[p,s] * y[p,s])
```

A secondary soft penalty discourages overlapping pairs of related sessions:

```text
maximize weighted_satisfaction - 2 * related_session_conflicts
```

Higher-ranked preferences receive larger weights, so attending a first-choice session contributes more than attending a lower-ranked session.

## Core Constraints

The implementation enforces all of the following requirements:

1. Every session is scheduled exactly once.
2. A two-slot session must remain within the same conference day.
3. A venue cannot host overlapping sessions.
4. A session may only use a venue whose capacity is at least the session capacity.
5. A session may only use a venue containing all required equipment.
6. A speaker must be available for every timeslot occupied by a session.
7. A speaker cannot present overlapping sessions.
8. A participant may attend only ranked sessions for which an attendance variable exists.
9. A participant must be available for every timeslot occupied by an attended session.
10. A participant cannot attend overlapping sessions.
11. Attendance assigned to a session cannot exceed the session capacity.
12. Related sessions are discouraged from overlapping through a soft objective penalty.

## Why This Model Corrects the Common Logical Errors

Several tempting formulations of conference scheduling are logically invalid. This implementation avoids those errors explicitly.

- Python `any()` is never applied to CP-SAT expressions. CP-SAT expressions are symbolic and cannot be evaluated as ordinary Python booleans.
- Participant attendance is linked to the actual selected time-and-venue assignment rather than to an unrelated global session indicator.
- The one-session-per-timeslot constraint is based on the actual occupied timeslots of each selected session, including two-slot sessions.
- Venue capacity is treated as assignment compatibility, while session attendance capacity is enforced separately.
- Generated session durations are actually represented in venue occupancy, speaker conflicts, participant conflicts, and availability checks.
- Two-slot sessions cannot start in the last timeslot of a day.
- Speaker availability and room-equipment requirements are enforced before incompatible assignment variables are created.
- Attendance variables are created only for ranked sessions, reducing model size and avoiding meaningless attendance decisions.

## Independent Post-Solve Validation

The solver model is followed by an independent validation layer. After a feasible or optimal solution is found, the program checks exactly one placement for every session, day-boundary feasibility for multi-slot sessions, venue capacity and equipment compatibility, venue non-overlap, speaker availability, speaker non-overlap, participant availability, participant non-overlap, and session attendance capacity.

Any violation raises an assertion rather than being silently ignored.

## Installation

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install the dependency:

```bash
pip install -r requirements.txt
```

## Running the Model

```bash
python conference_scheduler.py
```

The program prints solver status, objective value, best objective bound, solution time, number of penalized related-session conflicts, the complete session schedule, venue assignments, attendance by session, aggregate preference-satisfaction statistics, and validation results.

## Reproducibility

The data generator uses seed `42` by default:

```python
data = build_synthetic_data(seed=42)
```

Changing the seed produces a different synthetic conference instance while preserving the same structural requirements.

## Solver Status

Because CP-SAT can be run with a finite time limit, the returned status can be either `OPTIMAL` or `FEASIBLE`.

- `OPTIMAL` means CP-SAT proved that no better objective value exists.
- `FEASIBLE` means a valid solution was found, but optimality was not proved within the time limit.

The program prints both the incumbent objective value and the best bound so that the quality of a time-limited solution can be assessed correctly.

## Mathematical Model

Let `S` be the set of sessions, `T` the timeslots, `V` the venues, `P` the participants, `A_s` the feasible start-time/venue assignments for session `s`, `D_s` the duration of session `s`, `R_p` the ranked sessions of participant `p`, and `w_ps` the preference weight.

The main placement constraint is

```text
sum_{(t,v) in A_s} x_stv = 1                 for all s in S
```

For each venue `v` and physical timeslot `tau`, overlapping placements satisfy

```text
sum x_stv <= 1
```

over every placement whose occupied interval contains `tau`.

Participant attendance is linked to the selected placement through `z` variables using

```text
z_pstv <= y_ps
z_pstv <= x_stv
z_pstv >= y_ps + x_stv - 1
```

and

```text
y_ps = sum z_pstv
```

over placements for which participant `p` is available for the entire duration of session `s`.

Participant overlap is prevented by

```text
sum z_pstv <= 1
```

for every participant and physical timeslot, again summing all attendance placements whose occupied intervals contain that timeslot.

Session capacity is

```text
sum_p y_ps <= capacity_s
```

The objective is

```text
maximize
    sum_{p,s} w_ps y_ps
    - lambda * sum(conflict variables)
```

where `lambda = 2` in the supplied instance.

## Educational Extensions

Useful advanced extensions include lexicographic or epsilon-constraint multiobjective optimization, fairness constraints across participants, track-level parallelism limits, walking-distance penalties between consecutive sessions, robust scheduling under uncertain attendance, chance-constrained room sizing, Benders decomposition for large variants, large-neighborhood search hybrids, and stochastic speaker-disruption scenarios.

## License

This repository is **not licensed for commercial use**.

It is distributed under the included Non-Commercial Academic License. Educational, personal, and academic research use is permitted subject to the terms in `LICENSE`. Commercial use, paid redistribution, SaaS incorporation, commercial consulting use, and internal production use by for-profit organizations require prior written permission from the copyright holder.

This is a source-available non-commercial license rather than an OSI-approved open-source license.
