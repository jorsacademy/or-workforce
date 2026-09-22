"""Optimal conference meeting scheduling with OR-Tools CP-SAT.

This educational example builds a synthetic but fully specified three-day
conference instance and solves a multi-constraint scheduling problem that
integrates session placement, room compatibility, speaker availability,
participant preferences, attendance assignment, and track-conflict penalties.

The instance is generated deterministically from a fixed random seed so that
students and instructors obtain reproducible results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
import random

from ortools.sat.python import cp_model


# ---------------------------------------------------------------------------
# Problem data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Venue:
    venue_id: int
    name: str
    capacity: int
    equipment: frozenset[str]


@dataclass(frozen=True)
class Session:
    session_id: int
    title: str
    track: str
    duration: int
    capacity: int
    speaker_id: int
    required_equipment: frozenset[str]
    session_type: str


@dataclass
class ConferenceData:
    participants: List[int]
    speakers: List[int]
    sessions: Dict[int, Session]
    venues: Dict[int, Venue]
    timeslots: List[int]
    day_of_slot: Dict[int, int]
    position_in_day: Dict[int, int]
    participant_availability: Dict[int, Set[int]]
    speaker_availability: Dict[int, Set[int]]
    preferences: Dict[int, List[int]]
    preference_weight: Dict[Tuple[int, int], int]
    related_session_pairs: List[Tuple[int, int]]


# ---------------------------------------------------------------------------
# Deterministic synthetic data generation
# ---------------------------------------------------------------------------


def build_synthetic_data(seed: int = 42) -> ConferenceData:
    """Create a reproducible PhD-level conference scheduling instance."""

    rng = random.Random(seed)

    num_participants = 150
    num_sessions = 50
    slots_per_day = 5
    num_days = 3
    num_timeslots = slots_per_day * num_days

    participants = list(range(1, num_participants + 1))
    timeslots = list(range(1, num_timeslots + 1))

    day_of_slot = {
        t: (t - 1) // slots_per_day + 1
        for t in timeslots
    }
    position_in_day = {
        t: (t - 1) % slots_per_day + 1
        for t in timeslots
    }

    venues = {
        1: Venue(1, "Auditorium A", 140, frozenset({"projector", "stage", "streaming"})),
        2: Venue(2, "Auditorium B", 110, frozenset({"projector", "stage"})),
        3: Venue(3, "Lecture Hall C", 90, frozenset({"projector", "streaming"})),
        4: Venue(4, "Lecture Hall D", 80, frozenset({"projector"})),
        5: Venue(5, "Seminar Room E", 60, frozenset({"projector"})),
        6: Venue(6, "Seminar Room F", 55, frozenset({"projector", "whiteboard"})),
        7: Venue(7, "Workshop Lab G", 45, frozenset({"projector", "computers", "lab"})),
        8: Venue(8, "Workshop Lab H", 40, frozenset({"projector", "computers", "lab"})),
        9: Venue(9, "Innovation Studio I", 35, frozenset({"projector", "whiteboard", "robotics"})),
        10: Venue(10, "Meeting Room J", 30, frozenset({"projector", "whiteboard"})),
    }

    tracks = [
        "Artificial Intelligence",
        "Quantum Computing",
        "Bioinformatics",
        "Robotics",
        "Sustainability",
    ]

    speakers = list(range(1, 41))

    session_templates = [
        ("Keynote", 1, frozenset({"projector", "stage"}), (80, 140)),
        ("Workshop", 2, frozenset({"projector", "computers"}), (25, 45)),
        ("Technical", 1, frozenset({"projector"}), (30, 90)),
        ("Panel", 1, frozenset({"projector", "stage"}), (40, 110)),
        ("Lab", 2, frozenset({"projector", "lab"}), (20, 40)),
    ]

    sessions: Dict[int, Session] = {}
    for s in range(1, num_sessions + 1):
        track = tracks[(s - 1) % len(tracks)]

        # Ensure a controlled but varied mix of durations and room requirements.
        if s in {1, 11, 21, 31, 41}:
            session_type, duration, equipment, cap_range = session_templates[0]
        elif s % 7 == 0:
            session_type, duration, equipment, cap_range = session_templates[4]
        elif s % 5 == 0:
            session_type, duration, equipment, cap_range = session_templates[1]
        elif s % 4 == 0:
            session_type, duration, equipment, cap_range = session_templates[3]
        else:
            session_type, duration, equipment, cap_range = session_templates[2]

        capacity = rng.randint(cap_range[0], cap_range[1])
        speaker_id = speakers[(s - 1) % len(speakers)]

        # Robotics technical sessions occasionally require robotics equipment.
        if track == "Robotics" and session_type == "Technical" and s % 3 == 0:
            equipment = frozenset(set(equipment) | {"robotics"})
            capacity = min(capacity, 35)

        sessions[s] = Session(
            session_id=s,
            title=f"{track} {session_type} {s}",
            track=track,
            duration=duration,
            capacity=capacity,
            speaker_id=speaker_id,
            required_equipment=equipment,
            session_type=session_type,
        )

    # Speaker availability: each speaker is available for at least 10 of 15 slots.
    speaker_availability: Dict[int, Set[int]] = {}
    for speaker in speakers:
        unavailable = set(rng.sample(timeslots, 3))
        speaker_availability[speaker] = set(timeslots) - unavailable

    # Make all keynote speakers available in at least one early slot each day.
    early_slots = {1, 2, 6, 7, 11, 12}
    for session in sessions.values():
        if session.session_type == "Keynote":
            speaker_availability[session.speaker_id] |= early_slots

    # Participant availability: 11-14 available slots per participant.
    participant_availability: Dict[int, Set[int]] = {}
    for p in participants:
        available_count = rng.randint(11, 14)
        participant_availability[p] = set(rng.sample(timeslots, available_count))

    # Participants rank seven preferred sessions. Preferences are biased toward
    # two latent favorite tracks so the instance contains meaningful conflicts.
    preferences: Dict[int, List[int]] = {}
    preference_weight: Dict[Tuple[int, int], int] = {}
    rank_weights = [10, 8, 6, 5, 4, 3, 2]

    sessions_by_track = {
        track: [s for s, data in sessions.items() if data.track == track]
        for track in tracks
    }

    for p in participants:
        favorite_tracks = rng.sample(tracks, 2)
        candidate_pool = list(
            dict.fromkeys(
                sessions_by_track[favorite_tracks[0]]
                + sessions_by_track[favorite_tracks[1]]
                + list(sessions.keys())
            )
        )
        ranked = rng.sample(candidate_pool, 7)
        preferences[p] = ranked
        for rank, session_id in enumerate(ranked):
            preference_weight[p, session_id] = rank_weights[rank]

    # Related sessions from the same track should preferably not overlap.
    # This is modeled as a soft conflict penalty rather than a hard restriction.
    related_session_pairs: List[Tuple[int, int]] = []
    for track in tracks:
        track_sessions = sessions_by_track[track]
        for idx in range(0, len(track_sessions) - 1, 2):
            related_session_pairs.append((track_sessions[idx], track_sessions[idx + 1]))

    return ConferenceData(
        participants=participants,
        speakers=speakers,
        sessions=sessions,
        venues=venues,
        timeslots=timeslots,
        day_of_slot=day_of_slot,
        position_in_day=position_in_day,
        participant_availability=participant_availability,
        speaker_availability=speaker_availability,
        preferences=preferences,
        preference_weight=preference_weight,
        related_session_pairs=related_session_pairs,
    )


# ---------------------------------------------------------------------------
# CP-SAT model
# ---------------------------------------------------------------------------


def feasible_start_slots(data: ConferenceData, session: Session) -> List[int]:
    """Return start slots that keep a session inside one conference day."""

    valid = []
    for t in data.timeslots:
        final_position = data.position_in_day[t] + session.duration - 1
        if final_position <= 5:
            valid.append(t)
    return valid


def occupied_slots(start: int, duration: int) -> List[int]:
    return list(range(start, start + duration))


def solve_conference(data: ConferenceData, time_limit_seconds: float = 60.0):
    """Build and solve the conference scheduling model."""

    model = cp_model.CpModel()

    # x[s,t,v] = 1 iff session s starts at timeslot t in venue v.
    x: Dict[Tuple[int, int, int], cp_model.IntVar] = {}

    compatible_assignments: Dict[int, List[Tuple[int, int]]] = {}

    for s, session in data.sessions.items():
        compatible_assignments[s] = []
        for t in feasible_start_slots(data, session):
            session_slots = occupied_slots(t, session.duration)

            # Speaker must be available for every occupied slot.
            if not all(slot in data.speaker_availability[session.speaker_id] for slot in session_slots):
                continue

            for v, venue in data.venues.items():
                if venue.capacity < session.capacity:
                    continue
                if not session.required_equipment.issubset(venue.equipment):
                    continue

                x[s, t, v] = model.NewBoolVar(f"x_s{s}_t{t}_v{v}")
                compatible_assignments[s].append((t, v))

        if not compatible_assignments[s]:
            raise ValueError(f"Session {s} has no feasible time/venue assignment.")

    # Each session starts exactly once in exactly one compatible venue.
    for s in data.sessions:
        model.Add(
            sum(x[s, t, v] for t, v in compatible_assignments[s]) == 1
        )

    # Venue occupancy across multi-slot sessions.
    for v in data.venues:
        for tau in data.timeslots:
            active = []
            for s, session in data.sessions.items():
                for t, assigned_v in compatible_assignments[s]:
                    if assigned_v == v and tau in occupied_slots(t, session.duration):
                        active.append(x[s, t, v])
            if active:
                model.Add(sum(active) <= 1)

    # A speaker may not present two overlapping sessions.
    for speaker in data.speakers:
        speaker_sessions = [
            s for s, session in data.sessions.items() if session.speaker_id == speaker
        ]
        for tau in data.timeslots:
            active = []
            for s in speaker_sessions:
                duration = data.sessions[s].duration
                for t, v in compatible_assignments[s]:
                    if tau in occupied_slots(t, duration):
                        active.append(x[s, t, v])
            if active:
                model.Add(sum(active) <= 1)

    # y[p,s] = 1 iff participant p attends preferred session s.
    # Variables exist only for ranked sessions, reducing model size substantially.
    y: Dict[Tuple[int, int], cp_model.IntVar] = {}
    for p in data.participants:
        for s in data.preferences[p]:
            y[p, s] = model.NewBoolVar(f"y_p{p}_s{s}")

    # z[p,s,t,v] linearizes attendance together with the chosen session placement.
    z: Dict[Tuple[int, int, int, int], cp_model.IntVar] = {}

    for p in data.participants:
        for s in data.preferences[p]:
            session = data.sessions[s]
            feasible_attendance_terms = []

            for t, v in compatible_assignments[s]:
                slots = occupied_slots(t, session.duration)
                if all(slot in data.participant_availability[p] for slot in slots):
                    z[p, s, t, v] = model.NewBoolVar(f"z_p{p}_s{s}_t{t}_v{v}")
                    model.Add(z[p, s, t, v] <= y[p, s])
                    model.Add(z[p, s, t, v] <= x[s, t, v])
                    model.Add(z[p, s, t, v] >= y[p, s] + x[s, t, v] - 1)
                    feasible_attendance_terms.append(z[p, s, t, v])

            # Attendance is possible only if the selected placement is compatible
            # with the participant's availability for the entire session duration.
            if feasible_attendance_terms:
                model.Add(y[p, s] == sum(feasible_attendance_terms))
            else:
                model.Add(y[p, s] == 0)

    # Participants cannot attend overlapping sessions.
    for p in data.participants:
        for tau in data.timeslots:
            active = []
            for s in data.preferences[p]:
                session = data.sessions[s]
                for t, v in compatible_assignments[s]:
                    key = (p, s, t, v)
                    if key in z and tau in occupied_slots(t, session.duration):
                        active.append(z[key])
            if active:
                model.Add(sum(active) <= 1)

    # Session attendance capacity. Because every feasible venue is already at
    # least as large as the session capacity, the session capacity is binding.
    for s, session in data.sessions.items():
        interested = [p for p in data.participants if s in data.preferences[p]]
        if interested:
            model.Add(sum(y[p, s] for p in interested) <= session.capacity)

    # Soft penalty for scheduling related sessions at overlapping times.
    conflict_vars: List[cp_model.IntVar] = []
    for pair_index, (s1, s2) in enumerate(data.related_session_pairs, start=1):
        dur1 = data.sessions[s1].duration
        dur2 = data.sessions[s2].duration

        for t1, v1 in compatible_assignments[s1]:
            slots1 = set(occupied_slots(t1, dur1))
            for t2, v2 in compatible_assignments[s2]:
                if slots1.intersection(occupied_slots(t2, dur2)):
                    c = model.NewBoolVar(
                        f"related_conflict_{pair_index}_s{s1}_s{s2}_t{t1}_{t2}_v{v1}_{v2}"
                    )
                    model.Add(c <= x[s1, t1, v1])
                    model.Add(c <= x[s2, t2, v2])
                    model.Add(c >= x[s1, t1, v1] + x[s2, t2, v2] - 1)
                    conflict_vars.append(c)

    # Objective: maximize weighted preference satisfaction while discouraging
    # related-session overlap. Preference scores dominate conflict penalties.
    satisfaction = sum(
        data.preference_weight[p, s] * y[p, s]
        for p in data.participants
        for s in data.preferences[p]
    )
    conflict_penalty = 2 * sum(conflict_vars)
    model.Maximize(satisfaction - conflict_penalty)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 42

    status = solver.Solve(model)

    return model, solver, status, x, y, compatible_assignments, conflict_vars


# ---------------------------------------------------------------------------
# Solution extraction and validation
# ---------------------------------------------------------------------------


def extract_schedule(data, solver, x, compatible_assignments):
    schedule: Dict[int, Tuple[int, int]] = {}
    for s in data.sessions:
        chosen = [
            (t, v)
            for t, v in compatible_assignments[s]
            if solver.Value(x[s, t, v]) == 1
        ]
        if len(chosen) != 1:
            raise AssertionError(f"Session {s} has {len(chosen)} selected assignments.")
        schedule[s] = chosen[0]
    return schedule


def validate_solution(data, solver, status, x, y, compatible_assignments):
    """Run independent post-solve checks against all major model requirements."""

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"No feasible schedule. Solver status: {solver.StatusName(status)}")

    schedule = extract_schedule(data, solver, x, compatible_assignments)

    # Exactly one assignment per session and same-day duration feasibility.
    for s, (t, v) in schedule.items():
        session = data.sessions[s]
        slots = occupied_slots(t, session.duration)
        assert data.position_in_day[t] + session.duration - 1 <= 5
        assert all(data.day_of_slot[slot] == data.day_of_slot[t] for slot in slots)

        venue = data.venues[v]
        assert venue.capacity >= session.capacity
        assert session.required_equipment.issubset(venue.equipment)
        assert all(slot in data.speaker_availability[session.speaker_id] for slot in slots)

    # No venue overlap.
    for v in data.venues:
        for tau in data.timeslots:
            occupying = [
                s
                for s, (t, chosen_v) in schedule.items()
                if chosen_v == v and tau in occupied_slots(t, data.sessions[s].duration)
            ]
            assert len(occupying) <= 1, (v, tau, occupying)

    # No speaker overlap.
    for speaker in data.speakers:
        speaker_sessions = [s for s in data.sessions if data.sessions[s].speaker_id == speaker]
        for tau in data.timeslots:
            presenting = [
                s
                for s in speaker_sessions
                if tau in occupied_slots(schedule[s][0], data.sessions[s].duration)
            ]
            assert len(presenting) <= 1, (speaker, tau, presenting)

    # Attendance availability, non-overlap, preference membership, and capacity.
    session_attendance = {s: 0 for s in data.sessions}
    for p in data.participants:
        attended = [s for s in data.preferences[p] if solver.Value(y[p, s]) == 1]

        for s in attended:
            assert s in data.preferences[p]
            start, _ = schedule[s]
            slots = occupied_slots(start, data.sessions[s].duration)
            assert all(slot in data.participant_availability[p] for slot in slots)
            session_attendance[s] += 1

        for tau in data.timeslots:
            simultaneous = [
                s
                for s in attended
                if tau in occupied_slots(schedule[s][0], data.sessions[s].duration)
            ]
            assert len(simultaneous) <= 1, (p, tau, simultaneous)

    for s, attendance in session_attendance.items():
        assert attendance <= data.sessions[s].capacity, (s, attendance)

    return schedule, session_attendance


def print_report(data, solver, status, x, y, compatible_assignments, conflict_vars):
    schedule, session_attendance = validate_solution(
        data, solver, status, x, y, compatible_assignments
    )

    print("=" * 88)
    print("OPTIMAL CONFERENCE MEETING SCHEDULING - CP-SAT")
    print("=" * 88)
    print(f"Solver status      : {solver.StatusName(status)}")
    print(f"Objective value    : {solver.ObjectiveValue():.0f}")
    print(f"Best bound         : {solver.BestObjectiveBound():.0f}")
    print(f"Wall time (s)      : {solver.WallTime():.3f}")
    print(f"Conflicts penalized: {sum(solver.Value(c) for c in conflict_vars)}")
    print()

    print("SESSION SCHEDULE")
    print("-" * 88)
    for s in sorted(data.sessions):
        session = data.sessions[s]
        t, v = schedule[s]
        venue = data.venues[v]
        end_t = t + session.duration - 1
        print(
            f"Session {s:02d} | Day {data.day_of_slot[t]} | Slots {t:02d}-{end_t:02d} | "
            f"Venue {v:02d} {venue.name:<20} | {session.track:<24} | "
            f"{session.session_type:<9} | Attendance {session_attendance[s]:3d}/{session.capacity:3d}"
        )

    total_ranked = sum(len(data.preferences[p]) for p in data.participants)
    total_attended = sum(
        solver.Value(y[p, s])
        for p in data.participants
        for s in data.preferences[p]
    )
    weighted_satisfaction = sum(
        data.preference_weight[p, s] * solver.Value(y[p, s])
        for p in data.participants
        for s in data.preferences[p]
    )

    print()
    print("PARTICIPANT SATISFACTION")
    print("-" * 88)
    print(f"Ranked session requests        : {total_ranked}")
    print(f"Satisfied ranked attendances   : {total_attended}")
    print(f"Request satisfaction rate      : {100.0 * total_attended / total_ranked:.2f}%")
    print(f"Weighted preference score      : {weighted_satisfaction}")

    print()
    print("VALIDATION")
    print("-" * 88)
    print("All post-solve validation checks passed.")
    print("  - every session scheduled exactly once")
    print("  - multi-slot sessions remain within a single day")
    print("  - no venue overlap")
    print("  - room capacity and equipment compatibility satisfied")
    print("  - speaker availability and non-overlap satisfied")
    print("  - participant availability and non-overlap satisfied")
    print("  - session attendance capacities satisfied")


def main():
    data = build_synthetic_data(seed=42)
    model, solver, status, x, y, compatible_assignments, conflict_vars = solve_conference(
        data,
        time_limit_seconds=60.0,
    )
    print_report(data, solver, status, x, y, compatible_assignments, conflict_vars)


if __name__ == "__main__":
    main()
