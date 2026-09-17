# Workforce Optimization Research Series

This file maps workforce-related repositories across staffing, rostering, scheduling, queueing, and labor allocation. It is an index only: the repositories remain separate because they represent different operational decisions and different mathematical structures.

## Workforce planning and staffing

- `or-workforce` — applied workforce-analytics portfolio and cross-project entry point.
- `call-center-workforce-optimization` — service-system staffing with queueing/workforce decisions.
- `airport-checkin-counter-optimization-erlang-c` — queueing-based counter/staffing analysis using Erlang-C style logic.
- `metroglobal-airport-counter-optimization` — airport-counter optimization with a distinct application formulation.
- `airport-checkin-simulation-optimization` — staffing/capacity decisions evaluated through discrete-event simulation rather than a closed-form queueing model.

## Rostering and personnel scheduling

- `hybrid-personnel-scheduling-staff-rostering` — general personnel scheduling/rostering.
- `aviation-crew-scheduling-milp` — qualification, duty, rest, and mission-assignment MILP.
- `airline-crew-workforce-optimization-ga` — crew/workforce optimization using a genetic algorithm.
- `airline-crew-scheduling-column-generation` — large-scale crew scheduling through column generation.

## Production and operational labor allocation

- `assembly-line-balancing-optimizer-salbp` — labor/workstation balance through assembly-line structure rather than a generic roster.
- `parallel-machine-scheduling-milp-optimization` — machine scheduling with labor implications but primarily a scheduling model.
- `adaptive-production-scheduling-python` — dynamic scheduling context where labor/capacity may interact with operational adaptation.

## Why these repositories stay separate

They answer materially different questions:

- how many servers or counters are required;
- which person works which shift or mission;
- how legal/qualification/rest constraints shape feasible rosters;
- how workforce decisions interact with machine or production schedules;
- whether the operational system is modeled analytically, by MILP/CP, by metaheuristics, or by simulation.

A shared workforce domain is therefore a reason to cross-link projects, not to merge them automatically.
