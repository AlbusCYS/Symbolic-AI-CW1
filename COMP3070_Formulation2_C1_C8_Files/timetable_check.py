"""Independent, ordinary-Python timetable checks for C1-C8.

No Z3 expressions or solver eligibility helpers are used here.
"""

from itertools import combinations


def validate_timetable(instance, timetable):
    """Raise AssertionError for a violation; return None for a valid timetable."""
    assert timetable is not None, "SAT requires a timetable"
    assert len(timetable) == instance.number_of_exams, "Missing or extra exams"
    assert sorted(e for e, _, _ in timetable) == list(
        range(instance.number_of_exams)
    ), "Every exam must appear exactly once"

    fields = [getattr(instance, name, None) for name in (
        "exam_requirements", "room_facilities", "exam_durations", "slot_durations"
    )]
    has_metadata = any(value is not None for value in fields)
    assert not has_metadata or all(value is not None for value in fields), (
        "Incomplete C7/C8 metadata"
    )

    occupied = set()
    for exam, slot, room in timetable:
        assert 0 <= slot < instance.number_of_slots, "Invalid timeslot"
        assert 0 <= room < instance.number_of_rooms, "Invalid room"
        assert (slot, room) not in occupied, "Room double-booked"
        occupied.add((slot, room))
        students = {s for e, s in instance.exams_to_students if e == exam}
        assert len(students) <= instance.room_capacities[room], "Room too small"
        if has_metadata:
            for feature in instance.exam_requirements[exam]:
                assert feature in instance.room_facilities[room], (
                    f"C7: room {room} lacks {feature!r} for exam {exam}"
                )
            assert instance.exam_durations[exam] <= instance.slot_durations[slot], (
                f"C8: exam {exam} is longer than slot {slot}"
            )

    for student in range(instance.number_of_students):
        exams = {e for e, s in instance.exams_to_students if s == student}
        slots = [slot for exam, slot, _ in timetable if exam in exams]
        assert len(slots) == len(set(slots)), "Student has simultaneous exams"
        assert all(abs(a - b) > 1 for a, b in combinations(slots, 2)), (
            "Student has consecutive exams"
        )
