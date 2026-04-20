from enum import Enum


class UserRole(str, Enum):
    student = "student"
    trainer = "trainer"
    institution = "institution"
    programme_manager = "programme_manager"
    monitoring_officer = "monitoring_officer"


class AttendanceStatus(str, Enum):
    present = "present"
    absent = "absent"
    late = "late"
