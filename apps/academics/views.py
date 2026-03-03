from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .services import enroll_student, unenroll_student, add_to_cart
from ..finance.services import  calculate_cart_total,generate_fee_voucher
from .services import remove_course_from_cart
from django.contrib.auth.decorators import login_required
from .models import Course,CourseBySection, Semester, Enrollment
from ..finance.models import VoucherItem, FeeVoucher
from .permissions import student_only, instructor_only
import stripe 
from django.conf import settings

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

    return render(request, 'temps/academics/pages/StudentDashboard/Overview.html')

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

@student_only
@login_required
def student_course_review_page(request):
    semesters = Semester.objects.filter(enrollments__student=request.user.student_profile).distinct()
    return render(request, 'temps/academics/pages/StudentDashboard/ReviewClassesBySemester.html',{'semesters':semesters,'page_name':'Review Classes'})

@student_only
@login_required
def student_course_by_semester_page_view(request, semester_id):
    semester = get_object_or_404(Semester, id=semester_id )
    assignments = semester.assignments.filter(course_by_section__enrollments__student= request.user.student_profile)
    enrollments0 = semester.enrollments.filter(student= request.user.student_profile)
    enrollments = []
    for enrollment in enrollments0:
        for assignment in assignments:
            if enrollment.course_by_section == assignment.course_by_section:
                enrollment.__setattr__('assignment',assignment)
                enrollments.append(enrollment)
    
    return render(request, 'temps/academics/pages/StudentDashboard/ReviewClasses.html',{'enrollments':enrollments,'semester':semester,'assignments':assignments, 'page_name':'Review Classes'})

@student_only
@login_required
def student_enrolled_course_details_view(request, semester_id,course_code_by_section):
    semester = get_object_or_404(Semester, id=semester_id)
    course_by_section = get_object_or_404(CourseBySection, course_code_by_section=course_code_by_section)
    enrollment = get_object_or_404(course_by_section.enrollments, student=request.user.student_profile, semester=semester)
    assignment = get_object_or_404(course_by_section.assignments,semester=semester)
    marks = enrollment.marks.all()
    print(enrollment)
    return render(request, 'temps/academics/pages/StudentDashboard/EnrolledCourseDetails.html',{'enrollment':enrollment,'semester':semester,'course_by_section':course_by_section,'assignment':assignment,'marks':marks})

@student_only
@login_required
def course_detail_page_view(request, course_code_by_section):
    course = get_object_or_404(CourseBySection, course_code_by_section=course_code_by_section)
    assignments = course.assignments.latest('assigned_at')
    return render(request ,'temps/academics/pages/StudentDashboard/CourseDetails.html',{'course':course,'assignment':assignments})

@student_only
@login_required
def student_drop_course_view(request, enrollment_id):
    try:
        unenroll_student(enrollment_id)
        messages.success(request,"Dropped course Successfully")
        return redirect("review_classes_by_semester")
    except Exception as e:
        messages.error(request, e)
        return redirect("review_classes_by_semester")
    
@student_only
@login_required
def add_to_cart_view(request, course_by_section_id):
    try:
        add_to_cart(request.user.student_profile, course_by_section_id)
        messages.success(request,'The course has been added to the cart')
    except Exception as e:
        messages.error(request, e)
    print("hello")
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