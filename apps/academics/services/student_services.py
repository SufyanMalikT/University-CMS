from django.db import transaction
from ..models import CourseBySection, Semester, Enrollment, MarkEntry, AttendanceEntry, Course
from ...accounts.models import Student
from ...finance.models import VoucherItem, FeeConfiguration, Ledger
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
@transaction.atomic 
def StudentRegistration(valid_form):
    user = valid_form.save(commit=False)
    password = valid_form.cleaned_data['password']
    user.set_password(password)
    user.save()
    student = Student.objects.create(user=user)
    student.save()
    return student



@transaction.atomic 
def add_to_cart(student, section_id):
    course_by_section = CourseBySection.objects.select_for_update().get(course_code_by_section=section_id)

    if course_by_section.available_seats <= 0:
        raise ValidationError('All the seats are either taken or booked.')
    
    if Enrollment.objects.filter(student=student, course_by_section_id=section_id).exists():
        raise ValidationError('You are already enrolled in this course.')
    
    obj, created = VoucherItem.objects.get_or_create(
        student=student,
        course_by_section=course_by_section,
        fee_voucher=None
    )
    
    if not created:
        raise ValidationError('The course is already in the cart')
    
    return obj

     
def remove_course_from_cart(student, item_id:int ):
    voucher_item = get_object_or_404(VoucherItem, id=item_id, student=student)
    if voucher_item.fee_voucher is not None:
        raise Exception("Cannot remove an item that is already linked to a fee voucher")

    voucher_item.delete()



@transaction.atomic
def enroll_student(student, course_code_by_section):
    # 1. fetch the course that student wants to enroll
    course_by_section = get_object_or_404(CourseBySection, course_code_by_section=course_code_by_section)
    semester = Semester.latest_semester()

    # 2. Checking if the deadline has passed for enrollment
    if not semester.can_add_course:
        raise ValidationError("Cannot enroll in this class at this time")
    
    # 3. Checking if the class limit has reached
    if course_by_section.no_of_enrolled_students >= course_by_section.section.limit_of_students:
        raise ValidationError("No seats available for this class")
    
    # 4. Fetching the global fee configurations 
    fee_per_credit = FeeConfiguration.objects.filter(name='per_credit').first() or 100
    exam_fee = FeeConfiguration.objects.filter(name='exam_fee').first() or 30
    
    # 5. Checking if the enrollment already exists otherwise creating a new one
    obj, created = Enrollment.objects.get_or_create(
        course_by_section=course_by_section, 
        semester=semester, student=student,
        fee_amount=(fee_per_credit.amount or 100)*course_by_section.course.credit_hours,
        exam_fee=(exam_fee.amount or 30),
        status='active'
    )

    # 6. If an enrollment already exists throwing an excaption as student is already enrolled in the course
    if not created:
        raise ValidationError("You are already enrolled in this class")
    
    # 7. Updating the cached_balance
    # this needs to be updated because student dropping the will increase the students debit which 
    # represents negative cached_balance
    student.cached_balance += obj.fee_amount + obj.exam_fee
    student.save()


    # 8. Creating a Ledger
    # a ledger needs to be created because we want to keep the record of students debit and credit
    Ledger.objects.create(
        student=student,
        enrollment=obj,
        amount=obj.fee_amount+obj.exam_fee,
        transaction_type='charge'
    )

    # 9. Updating the seat count
    course_by_section.no_of_enrolled_students += 1
    course_by_section.save()



@transaction.atomic
def unenroll_student(student, enrollment_id):
    # 1. Use select_for_update on BOTH objects to lock them for this transaction
    # This prevents balance/seat count glitches
    enrollment = Enrollment.objects.select_for_update().get(id=enrollment_id, student=student)
    
    if enrollment.status == 'dropped':
        return # Already dropped, do nothing

    if not enrollment.semester.can_drop_course:
        raise ValidationError("The drop deadline for this semester has passed.") 

    # 2. Update Enrollment Status
    enrollment.status = 'dropped'
    enrollment.save()

    # 3. Updating the seat count
    section = enrollment.course_by_section
    section.no_of_enrolled_students -= 1
    section.save()

    # 4. Updating the cached_balance
    # this needs to be updated because student dropping the will increase the students debit which 
    # represents negative cached_balance
    print(-(enrollment.fee_amount+enrollment.exam_fee))
    student.cached_balance -= enrollment.fee_amount + enrollment.exam_fee
    student.save()
    print(student.cached_balance)

    # 5. Creating a Ledger
    # a ledger needs to be created because we want to keep the record of students debit and credit
    Ledger.objects.create(
        student=student,
        enrollment=enrollment,
        amount=-(enrollment.fee_amount+enrollment.exam_fee),
        transaction_type ='refund'
    )



def grade_per_course(student, course_by_section):
    mark_entries = MarkEntry.objects.filter(enrollment__student=student, enrollment__course_by_section=course_by_section)

    if not mark_entries.exists():
        return None
    total_marks = 0
    obtained_marks = 0
    for entry in mark_entries:
        obtained_marks += entry.obtained_marks
        total_marks += entry.total_marks
    
    score = (total_marks/obtained_marks) * 100

    if score > 90:
        weight = 4.0
    elif score >= 80:
        weight = 3.66
    elif score >= 75:
        weight = 3.33
    elif score >= 70:
        weight = 3.0
    elif score >= 64:
        weight = 2.8
    elif score >= 60: # Fixed the logical overlap here
        weight = 2.5
    elif score >= 58:
        weight = 2.3
    elif score >= 54:
        weight = 2.1
    elif score >= 50:
        weight = 2.0
    else:
        weight = 0.0  # Failed course

    return weight

def grade_per_semester(student, semester):
    enrollments = semester.enrollments.filter(student=student,status='active',marks__is_locked=True)
    
    if not enrollments.exists():
        return 0
    total_semester_credit_hours = 0
    grade_points = 0
    for enrollment in enrollments:
        grade_points += enrollment.gpa*enrollment.course_by_section.course.credit_hours
        total_semester_credit_hours += enrollment.course_by_section.course.credit_hours
    sgpa = grade_points/total_semester_credit_hours
    return sgpa

def calculate_overall_attendance_percentage(student):
    # 1. Get all attendance records for THIS student across all their courses
    attendance_stats = AttendanceEntry.objects.filter(
        student=student,
        session__schedule__course_by_section__enrollments__status='active'
    ).aggregate(
        total_sessions=Count('id'),
        present_count=Count('id', filter=Q(was_present=True))
    )

    total = attendance_stats['total_sessions'] or 0
    present = attendance_stats['present_count'] or 0

    # 2. Safety check for Zero Division
    if total == 0:
        return 0

    return (present / total) * 100


def calculate_course_attendance(student, course_by_section):
    enrollment = Enrollment.objects.filter(student=student, course_by_section=course_by_section, status='active')
    if not enrollment.exists:
        raise Exception("Student is not enrolled in this course")
    attendance_stats = AttendanceEntry.objects.filter(
        student=student, 
        session__schedule__course_by_section=course_by_section
        ).aggregate(
            total_sessions=Count('id'),
            present_count=Count('id',filter=Q(was_present=True))
        )
    
    total_session = attendance_stats['total_sessions'] or 0
    present_count = attendance_stats['present_count'] or 0

    if total_session == 0:
        return 0
    
    return (present_count/total_session)*100
    
def student_marks_list_per_course_type(student):
    # Fetch all active enrollments for the student in one go
    # We use select_related to grab the course and category in the same query
    active_enrollments = student.enrollments.filter(status='active').select_related('course_by_section__course')

    # One loop through the categories, but NO database hits inside it
    stats_dict = {
        val: [e.percentage for e in active_enrollments if e.course_by_section.course.category == cat]
        for cat, val in Course.CATEGORY_CHOICES
    }
    return stats_dict