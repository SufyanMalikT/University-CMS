from ..models import ClassSession, Semester, CourseAssignment, AttendanceEntry
from ...accounts.models import Student
from django.shortcuts import get_object_or_404
from django.db import transaction
@transaction.atomic
def mark_attendance(course_by_section,schedule, date, absent_students=[]):
    semester = Semester.latest_semester()
    assignment = course_by_section.assignments.filter(semester=semester).first()
    session = ClassSession.objects.create(instructor=assignment.instructor, schedule=schedule, date=date)

    students = Student.objects.filter(enrollments__course_by_section=course_by_section, enrollments__semester=semester, enrollments__status='active')

    absent_students_id = [int(student_id) for student_id in absent_students]
    for student in students:
        if student.id in absent_students_id: 
            AttendanceEntry.objects.create(session=session, student=student,was_present=False)
        else:
            AttendanceEntry.objects.create(session=session, student=student)
        