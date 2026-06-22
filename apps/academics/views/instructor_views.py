from django.shortcuts import render, redirect
from ..permissions import instructor_only
from django.contrib.auth.decorators import login_required
from ..models import CourseBySection, CourseAssignment, Semester, ClassSchedule, Enrollment, \
      MarkEntry, Assessment
from ...accounts.models import Student
from django.shortcuts import get_object_or_404
from ..services.instructor_services import mark_attendance
from django.contrib import messages
@login_required
@instructor_only
def instructor_overview_page(request):
    return render(request, 'temps/academics/pages/InstructorDashboard/Overview.html', {})


@login_required
@instructor_only
def classes_details_page(request, class_id):
    course_by_section = get_object_or_404(CourseBySection, course_code_by_section=class_id)
    pending_grading = None
    if course_by_section.pending_grading is not None:
        pending_grading = course_by_section.pending_grading
    return render(request, 'temps/academics/pages/InstructorDashboard/classes-details.html',{'class':course_by_section,'pending_grading':pending_grading})


@login_required
@instructor_only
def attendance_page_for_class(request, course_by_section_id):
    course_by_section = get_object_or_404(CourseBySection, course_code_by_section=course_by_section_id)
    enrolled_students = Student.objects.filter(
        enrollments__semester=Semester.latest_semester(),
        enrollments__course_by_section=course_by_section,
        enrollments__status='active'
    )
    class_schedules = ClassSchedule.objects.filter(course_by_section=course_by_section, semester=Semester.latest_semester())
    return render(request, 'temps/academics/pages/InstructorDashboard/attendance_page.html',{'enrolled_students':enrolled_students ,'class':course_by_section, 'schedules':class_schedules})

@login_required
@instructor_only
def mark_attendance_view(request, course_by_section_id):
    if request.method == 'POST':
        try: 
            absent_students = request.POST.getlist('absent_students')
            session_date = request.POST.get('session_date')
            schedule_id = request.POST.get('schedule')
            
            course_by_section = get_object_or_404(CourseBySection, course_code_by_section=course_by_section_id)
            schedule = get_object_or_404(ClassSchedule, id=schedule_id)

            mark_attendance(course_by_section, schedule, session_date, absent_students)

            messages.success(request, "Attendance has been marked for this session")
            return redirect('academics/instructor:assigned_classes')
        except Exception as e:
            messages.error(request, "Error: "+str(e))
        return redirect('academics/instructor:attendance_page_for_class', course_by_section_id=course_by_section_id)
    


@login_required
@instructor_only
def assigned_courses_page(request):
    current_sem = Semester.latest_semester()
    assignments = CourseAssignment.objects.filter(instructor=request.user.instructor_profile,semester__in=[current_sem,Semester.previous_semester()])
    return render(request, 'temps/academics/pages/InstructorDashboard/assigned_classes.html',{'assignments':assignments,'current_sem':current_sem})

@instructor_only
def marks_upload_page(request, course_code_by_section):
    semester = Semester.latest_semester()
    course_by_section = get_object_or_404(CourseBySection, course_code_by_section = course_code_by_section)
    enrollments = Enrollment.objects.filter(semester=semester,status='active',course_by_section__course_code_by_section=course_code_by_section)
    return render(request, "temps/academics/pages/InstructorDashboard/marks.html",{'enrollments':enrollments,'course_by_section':course_by_section})

def assessment_management_page_view(request, course_code_by_section):
    course_by_section = get_object_or_404(CourseBySection, course_code_by_section=course_code_by_section)

    assessments = Assessment.objects.filter(course_by_section__course_code_by_section=course_by_section)
    return render(request,'temps/academics/pages/InstructorDashboard/assessment_management.html',{} )