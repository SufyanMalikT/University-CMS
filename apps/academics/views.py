from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .services import enroll_student, unenroll_student, add_to_cart
from ..finance.services import  calculate_cart_total,generate_fee_voucher
from .services import remove_course_from_cart, grade_per_course, \
                        calculate_overall_attendance_percentage, calculate_course_attendance
from django.contrib.auth.decorators import login_required
from .models import Course,CourseBySection, Semester, Enrollment
from ..finance.models import VoucherItem, FeeVoucher
from .permissions import student_only, instructor_only
import stripe 
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Q

stripe.api_key = settings.STRIPE_SECRET_KEY

def home_view(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('login')
    
    if hasattr(user, 'student_profile'):
        return redirect('student_dashboard')
    
    if hasattr(user, 'instructor_profile'):
        return redirect('home')
    return render(request, 'temps/academics/home.html')

@login_required
@student_only
def student_dashboard_view(request):
    attendance_percentage = calculate_overall_attendance_percentage(request.user.student_profile)
    return render(request, 'temps/academics/pages/StudentDashboard/Overview.html',{'page_name':'Overview','attendance_percentage':attendance_percentage})

@student_only
@login_required
def student_add_courses_page_view(request):
    course_by_section = None
    course_by_section_assignment = None
    unpaid_voucher = FeeVoucher.objects.filter(student=request.user.student_profile, status='unpaid')
    if request.method == "POST":
        if unpaid_voucher.exists():
            messages.error(request, "You have a pending fee voucher. You can\'t add courses till you pay your fee.")
            return redirect('add_classes')
        course_code = request.POST.get('course_search')
        try:
            course_by_section = get_object_or_404(CourseBySection,course_code_by_section=course_code)
            sem = Semester.latest_semester()
            course_by_section_assignment = course_by_section.assignments.filter(semester__session=sem.session,semester__start_date__month=sem.start_date.month).first()
            if not course_by_section_assignment:
                course_by_section_assignment = None
        except:
            return redirect('add_classes')

    
    return render(request, 'temps/academics/pages/StudentDashboard/AddClasses.html',{'course':course_by_section,'course_assignment_for_current_sem':course_by_section_assignment, 'page_name':'Add Classes'})

@student_only
@login_required
def student_add_courses_view(request, course_code_by_section):
    try:
        enroll_student(request.user.student_profile, course_code_by_section)
        messages.success(request,"Enrollment Successful!")
        return redirect('add_classes')
    except Exception as e:
        messages.error(request,e)
        return redirect('add_classes')

def student_course_details_view(request, course_code_by_section):
    course_by_section = get_object_or_404(CourseBySection, course_code_by_section=course_code_by_section)
    return render(request, 'temps/academics/pages/StudentDashboard/CourseDetails.html',{'course':course_by_section})
@student_only
@login_required
def student_course_review_page(request):
    student = request.user.student_profile
    
    # We filter Semesters to only those the student participated in
    # Then we annotate a count specifically for THIS student's enrollments
    semesters = Semester.objects.filter(
        enrollments__student=student
    ).annotate(
        user_course_count=Count(
            'enrollments', 
            filter=Q(enrollments__student=student,enrollments__status='active')
        )
    ).distinct().order_by('-start_date')
    return render(request, 'temps/academics/pages/StudentDashboard/ReviewClassesBySemester.html',{'semesters':semesters,'page_name':'Review Classes'})

@student_only
@login_required
def student_course_by_semester_page_view(request, semester_id):
    semester = get_object_or_404(Semester, id=semester_id )
    assignments = semester.assignments.filter(course_by_section__enrollments__student= request.user.student_profile).distinct()
    enrollments0 = semester.enrollments.filter(student= request.user.student_profile)
    enrollments = []
    for enrollment in enrollments0:
        for assignment in assignments:
            if enrollment.course_by_section == assignment.course_by_section:
                enrollment.__setattr__('assignment',assignment)
                enrollments.append(enrollment)
                print(enrollment.id)
    return render(request, 'temps/academics/pages/StudentDashboard/SemesterCourses.html',{'enrollments':enrollments,'semester':semester,'assignments':assignments, 'page_name':'Review Classes'})

@student_only
@login_required
def student_enrolled_course_detail_page_view(request, enrollment_id):
    student = request.user.student_profile
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    assignment = get_object_or_404(enrollment.course_by_section.assignments,semester=enrollment.semester)
    marks = enrollment.marks.all()
    attendance = calculate_course_attendance(student, enrollment.course_by_section)
    return render(request, 'temps/academics/pages/StudentDashboard/EnrolledCourseDetails.html',{'enrollment':enrollment,'assignment':assignment, 'attendance':attendance,'page_name':'Enrolled Course Details'})

@student_only
@login_required
def student_drop_course_page(request):
    semester = Semester.latest_semester()
    enrollments = None
    if semester.can_drop_course:
        enrollments = Enrollment.objects.filter(student=request.user.student_profile,status='active',semester=semester)
    if request.method == "POST":
        enrollment_id = request.POST.get('enrollment_ids',None)
        if enrollment_id:
            try:
                unenroll_student(request.user.student_profile, enrollment_id)
                messages.success(request, "Dropped the course successfully!")
            except Exception as e:
                messages.error(request, str(e))
            return redirect('drop_course')
        messages.error(request, "coundn't find the course to drop")
        return redirect('drop_course')
    return render(request, 'temps/academics/pages/StudentDashboard/DropClasses.html',{'semester':semester,'enrollments':enrollments})
    
@student_only
@login_required
def add_to_cart_view(request, course_by_section_id):
    is_already_enrolled = Enrollment.objects.filter(student=request.user.student_profile,course_by_section__course_code_by_section=course_by_section_id,semester=Semester.latest_semester(),status='active').exists()
    print(is_already_enrolled)
    if is_already_enrolled:
        messages.error(request, "Cannot add to cart. You are already enrolled in this course")
        return redirect("add_classes")
    try:
        add_to_cart(request.user.student_profile, course_by_section_id)
        messages.success(request,'The course has been added to the cart')
    except Exception as e:
        messages.error(request, e)
    return redirect('add_classes')


@student_only
@login_required
def cart_page_view(request):
    cart_total = calculate_cart_total(request.user.student_profile)
    unpaid_voucher = FeeVoucher.objects.filter(student=request.user.student_profile,status='unpaid').first()
    if request.method == "POST":
        try:
            voucher = generate_fee_voucher(request.user.student_profile)
            messages.success(request, 'The Fee Voucher has been generated')
            return redirect('download_fee_voucher',voucher_id=voucher.id)
        except Exception as e:
            messages.error(request, str(e))
            return redirect('cart')
    return render(request, 'temps/academics/pages/StudentDashboard/Cart.html',{ 'cart_total':cart_total,'unpaid_voucher':unpaid_voucher,'page_name':'Your Cart'})

@student_only
@login_required
def remove_course_from_cart_view(request, item_id):
    try:
        remove_course_from_cart(request.user.student_profile, item_id)
        messages.success(request, "The course has been removed from your cart")
    except Exception as e:
        messages.error(request,str(e))

    return redirect('cart')





@student_only 
@login_required
def enrolled_class_details_page_view(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)

    return render(request, 'temps/academics/pages/StudentDashbaord/EnrolledClassDetials.html',{'enrollment':enrollment})

@student_only
@login_required
def results_page_view(request):
    return render(request,'temps/academics/pages/StudentDashboard/Results.html',{})