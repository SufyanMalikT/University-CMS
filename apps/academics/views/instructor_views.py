from django.shortcuts import render, redirect
from ..permissions import instructor_only, assessment_updation_deletion, upload_and_update_marks
from django.contrib.auth.decorators import login_required
from ..models import CourseBySection, CourseAssignment, Semester, ClassSchedule, Enrollment, \
      MarkEntry, Assessment
from ...accounts.models import Student
from django.shortcuts import get_object_or_404
from ..services.instructor_services import mark_attendance, save_students_marks
from django.contrib import messages
from ..forms.instructor_forms import AssessmentForm, MarkEntryForm
from django.forms import formset_factory

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


@login_required
@instructor_only
def assessment_management_page_view(request, course_code_by_section):
    course_by_section = get_object_or_404(CourseBySection, course_code_by_section=course_code_by_section)

    assessments = Assessment.objects.filter(course_by_section=course_by_section)
    if not Semester.latest_semester().is_past_deadline_for_grading:
        form = AssessmentForm(request.POST or None,course_by_section=course_by_section)
        if request.method == 'POST':
            if form.is_valid():
                form.save()
    return render(request,'temps/academics/pages/InstructorDashboard/assessment_management.html',{'course_by_section':course_by_section,'assessments':assessments,'form':form} )

@login_required
@instructor_only
@assessment_updation_deletion
def update_assessment_page_view(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)
    form = AssessmentForm(request.POST or None, instance=assessment,course_by_section=assessment.course_by_section)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request,"Assessment Updated Successfully!")
            return redirect('academics/instructor:assessment_management',course_code_by_section=assessment.course_by_section.course_code_by_section)
        else:
            messages.error(request,form.errors)
            return redirect('academics/instructor:update_assessment',pk=pk)
    return render(request, 'temps/academics/pages/InstructorDashboard/update_assessment.html',{'form':form,'assessment':assessment})

@login_required
@instructor_only
@assessment_updation_deletion
def delete_assessment_view(request, pk):
    try:
        assessment = get_object_or_404(Assessment, pk=pk)
        assessment.delete()
        messages.success(request, "Assessment is deleted successfully!")
    except:
        messages.error(request, "No such assessment exists!")
    return redirect(request.META.get('HTTP_REFERER','/'))

@login_required
@instructor_only
@upload_and_update_marks
def mark_entry_by_assessment_page_view(request,pk):
    assessment = get_object_or_404(Assessment, pk=pk)
    enrollments = assessment.course_by_section.enrollments.filter(status='active').select_related('student__user')
    MarkEntryFormSet = formset_factory(
        MarkEntryForm,
        extra=len(enrollments)
    )
    if request.method == 'POST':
        formset = MarkEntryFormSet(
            request.POST
        )
        if formset.is_valid():
            save_students_marks(assessment=assessment, enrollments=enrollments, formset=formset)
            messages.success(request,"Successfully saved all the entries!")
            return redirect('academics/instructor:upload_marks_by_assessment', pk=assessment.id)
        else:
            messages.error(request,formset.error_messages)
            return redirect('academics/instructor:upload_marks_by_assessment', pk=assessment.id)
    else:
        initial = []

        for enrollment in enrollments:
            mark_entry = MarkEntry.objects.filter(
                enrollment=enrollment,
                assessment=assessment
            ).first()

            initial.append({
                'obtained_marks':mark_entry.obtained_marks if mark_entry else 0
            })
        formset = MarkEntryFormSet(
            initial=initial,
        )

    data = zip(enrollments, formset)
    return render(request, 'temps/academics/pages/InstructorDashboard/marks_by_assessments.html',{'data':data,'formset':formset,'assessment':assessment})

@login_required
@instructor_only
def grade_book_by_section(request,pk):
    course_by_section = get_object_or_404(CourseBySection, pk=pk)
    assessments = course_by_section.assessments.all()

    gradebook = []
    enrollments = course_by_section.enrollments.filter(status='active')

    for enrollment in enrollments:
        row = {   
            'enrollment':enrollment
        }
        for assessment in assessments:
            row = row | {
                f'{assessment.title}':assessment.mark_entries.filter(enrollment__student=enrollment.student)
            }
        row = row | {
            'grade':enrollment.grade
        }
        gradebook.append(row)
    return render(request, 'temps/academics/pages/InstructorDashboard/grade_book.html',{'course_by_section':course_by_section,'assessments':assessments,'gradebook':gradebook})