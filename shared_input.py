"""Shared input contract for both formulations, with no dependency on Z3.

The text format and enrolment order (exam_id, student_id) follow the supplied
Moodle template. The optional JSON format is our proposed group extension.
"""

import json
import re
from pathlib import Path


METADATA_FIELDS = (
    "exam_requirements", "room_facilities", "exam_durations", "slot_durations"
)


class Instance:
    def __init__(self):
        self.number_of_students = 0
        self.number_of_exams = 0
        self.number_of_slots = 0
        self.number_of_rooms = 0
        self.room_capacities = []
        self.exams_to_students = []
        self.exam_requirements = None
        self.room_facilities = None
        self.exam_durations = None
        self.slot_durations = None
        self.metadata_mode = None


def prepare_metadata(instance):
    """Validate and normalize the four fields, or supply neutral baseline data.

    Calling this from either solver also supports the original Instance class.
    Baseline values are synthetic assumptions, not facts supplied by Moodle.
    Feature matching is case-sensitive; names are not silently corrected.
    """
    values = [getattr(instance, name, None) for name in METADATA_FIELDS]
    if all(value is None for value in values):
        values = [
            [[] for _ in range(instance.number_of_exams)],
            [[] for _ in range(instance.number_of_rooms)],
            [60] * instance.number_of_exams,
            [120] * instance.number_of_slots,
        ]
        mode = "baseline"
    elif any(value is None for value in values):
        raise ValueError("C7/C8 metadata must include all four fields.")
    else:
        mode = getattr(instance, "metadata_mode", None) or "extended"

    expected_lengths = (
        instance.number_of_exams, instance.number_of_rooms,
        instance.number_of_exams, instance.number_of_slots,
    )
    normalized = []
    for name, value, count in zip(METADATA_FIELDS, values, expected_lengths):
        if not isinstance(value, (list, tuple)) or len(value) != count:
            raise ValueError(f"{name} must contain exactly {count} entries.")
        if name in ("exam_requirements", "room_facilities"):
            rows = []
            for row in value:
                if not isinstance(row, (list, tuple, set, frozenset)) or any(
                    not isinstance(feature, str) or not feature.strip()
                    or feature != feature.strip() for feature in row
                ):
                    raise ValueError(
                        f"{name} entries must be collections of nonempty feature "
                        "names without surrounding whitespace."
                    )
                rows.append(set(row))
            normalized.append(rows)
        else:
            if any(type(minutes) is not int or minutes <= 0 for minutes in value):
                raise ValueError(f"{name} must contain positive integer minutes.")
            normalized.append(list(value))

    for name, value in zip(METADATA_FIELDS, normalized):
        setattr(instance, name, value)
    instance.metadata_mode = mode
    return instance


def load_metadata(instance, filename):
    """Apply a complete JSON file; invalid input is an error, not UNSAT."""
    with open(filename, encoding="utf-8") as handle:
        metadata = json.load(handle)
    if not isinstance(metadata, dict) or set(metadata) != set(METADATA_FIELDS):
        raise ValueError("Metadata JSON must contain exactly: " + ", ".join(METADATA_FIELDS))
    for name in METADATA_FIELDS:
        setattr(instance, name, metadata[name])
    if any(metadata[name] is None for name in METADATA_FIELDS):
        raise ValueError("Metadata fields cannot be null.")
    instance.metadata_mode = "extended"
    return prepare_metadata(instance)


def read_file(filename, metadata_filename=None, *, baseline=False):
    """Read the original .txt file and, by default, its <stem>.extra.json.

    An explicitly supplied metadata path must exist. baseline=True deliberately
    ignores a companion file and uses the neutral C1-C6-equivalent assumptions.
    """
    if baseline and metadata_filename is not None:
        raise ValueError("Choose either baseline mode or a metadata file.")

    def read_attribute(name):
        line = handle.readline()
        match = re.fullmatch(re.escape(name) + r":\s*(\d+)\s*", line)
        if match:
            return int(match.group(1))
        raise ValueError(f"Could not parse {line!r}; expected {name}.")

    instance = Instance()
    with open(filename, encoding="utf-8") as handle:
        instance.number_of_students = read_attribute("Number of students")
        instance.number_of_exams = read_attribute("Number of exams")
        instance.number_of_slots = read_attribute("Number of slots")
        instance.number_of_rooms = read_attribute("Number of rooms")
        for room in range(instance.number_of_rooms):
            instance.room_capacities.append(read_attribute(f"Room {room} capacity"))
        for line in handle:
            match = re.fullmatch(r"\s*(\d+)\s+(\d+)\s*", line)
            if not match:
                raise ValueError(f"Failed to parse registration: {line!r}")
            instance.exams_to_students.append((int(match[1]), int(match[2])))

    companion = Path(filename).with_suffix(".extra.json")
    if not baseline and metadata_filename is not None:
        return load_metadata(instance, metadata_filename)
    if not baseline and companion.exists():
        return load_metadata(instance, companion)
    return prepare_metadata(instance)


def validate_and_index(instance):
    """Validate a programmatic instance and build enrolment indexes for solvers.

    This validates the same input contract for both encodings. Repeated exam/student
    registrations count only once. The returned lists contain sets of student IDs
    per exam and exam IDs per student, respectively.
    """
    students = instance.number_of_students
    exams = instance.number_of_exams
    slots = instance.number_of_slots
    rooms = instance.number_of_rooms
    if any(type(value) is not int or value < 0
           for value in (students, exams, slots, rooms)):
        raise ValueError("Student, exam, slot and room counts must be non-negative integers.")
    if len(instance.room_capacities) != rooms:
        raise ValueError("Provide exactly one capacity for each room.")
    if any(type(capacity) is not int or capacity < 0
           for capacity in instance.room_capacities):
        raise ValueError("Room capacities must be non-negative integers.")

    prepare_metadata(instance)
    exam_students = [set() for _ in range(exams)]
    student_exams = [set() for _ in range(students)]
    for exam, student in instance.exams_to_students:
        if not (type(exam) is int and type(student) is int
                and 0 <= exam < exams and 0 <= student < students):
            raise ValueError(
                f"Registration ({exam}, {student}) contains an out-of-range ID."
            )
        exam_students[exam].add(student)
        student_exams[student].add(exam)
    return exam_students, student_exams
