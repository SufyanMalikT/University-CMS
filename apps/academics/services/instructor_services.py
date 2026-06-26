from ..models import ClassSession, Semester, CourseAssignment, AttendanceEntry,\
      CourseBySection, Assessment, AssessmentType, MarkEntry
from ...accounts.models import Student
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
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

@transaction.atomic 
def validate_and_add_assessments(course_code_by_section, title, assessment_type_id, total_marks):
    course_by_section = get_object_or_404(CourseBySection,course_code_by_section=course_code_by_section)
    assessment_type = get_object_or_404(AssessmentType,id=assessment_type_id)


    obj, created = Assessment.objects.get_or_create(
        title=title, 
        assessment_type=assessment_type,
        course_by_section=course_by_section,
        total_marks=total_marks
    )
    if not created:
        raise 
    

@transaction.atomic
def save_students_marks(assessment,enrollments, formset):
    if assessment.course_by_section.semester.is_past_deadline_for_grading:
        raise ValidationError("Grading deadline is passed grades can't be saved.")
    
    for enrollment, form in zip(enrollments, formset):
        obtained_marks = form.cleaned_data.get('obtained_marks')

        MarkEntry.objects.update_or_create(
            enrollment=enrollment,
            assessment=assessment,
            defaults={ # defaults fields are not used for lookup the object 
                'obtained_marks':obtained_marks
            }
        )

