from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from ..forms import StudentRegistrationForm, InstructorRegistrationForm
from django.contrib import messages
from ..services.StudentServices import StudentRegistration, enroll_student, unenroll_student, add_to_cart
from ..services.InstructorServices import InstructorRegistration
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from ..services.AdminServices import admin_only
from ..models import Course,CourseBySection, Semester, Enrollment, VoucherItem
from ..permissions import student_only, instructor_only

@login_required
@student_only
def student_dashboard_view(request):
    return render(request, 'temps/app1/StudentDashboard.html',{})

@student_only
@login_required
def student_add_courses_page_view(request):
    course_by_section = None
    course_by_section_assignment = None
    if request.method == "POST":
        course_code = request.POST.get('course_search')
        try:
            course_by_section = get_object_or_404(CourseBySection,course_code_by_section=course_code)
            sem = Semester.latest_semester()
            course_by_section_assignment = course_by_section.assignments.filter(semester__session=sem.session,semester__start_date__month=sem.start_date.month).first()
            if not course_by_section_assignment:
                course_by_section_assignment = None
        except:
            return redirect('add_classes')

    
    return render(request, 'temps/app1/pages/StudentDashboard/AddClasses.html',{'course':course_by_section,'course_assignment_for_current_sem':course_by_section_assignment})

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
    return render(request, 'temps/app1/pages/StudentDashboard/ReviewClassesBySemester.html',{'semesters':semesters})

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
    
    return render(request, 'temps/app1/pages/StudentDashboard/ReviewClasses.html',{'enrollments':enrollments,'semester':semester,'assignments':assignments})

@student_only
@login_required
def student_enrolled_course_details_view(request, semester_id,course_code_by_section):
    semester = get_object_or_404(Semester, id=semester_id)
    course_by_section = get_object_or_404(CourseBySection, course_code_by_section=course_code_by_section)
    enrollment = get_object_or_404(course_by_section.enrollments, student=request.user.student_profile, semester=semester)
    assignment = get_object_or_404(course_by_section.assignments,semester=semester)
    marks = enrollment.marks.all()
    print(enrollment)
    return render(request, 'temps/app1/pages/StudentDashboard/EnrolledCourseDetails.html',{'enrollment':enrollment,'semester':semester,'course_by_section':course_by_section,'assignment':assignment,'marks':marks})

@student_only
@login_required
def course_detail_page_view(request, course_code_by_section):
    course = get_object_or_404(CourseBySection, course_code_by_section=course_code_by_section)
    assignments = course.assignments.latest('assigned_at')
    return render(request ,'temps/app1/pages/StudentDashboard/CourseDetails.html',{'course':course,'assignment':assignments})

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
    

def add_to_cart_view(request, course_by_section_id):
    try:
        add_to_cart(request.user.student_profile, course_by_section_id)
        messages.success(request,'The course has been added to the cart')
    except Exception as e:
        messages.error(request, e)
    print("hello")
    return redirect('add_classes')

def cart_page_view(request):
    voucher_items = VoucherItem.objects.filter(student=request.user.student_profile, fee_voucher=None)
    
    return render(request, 'temps/app1/pages/StudentDashboard/Cart.html',{'voucher_items':voucher_items})