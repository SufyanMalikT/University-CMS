from django.contrib import admin
from .models import CustomUser, Student, Instructor, Semester, Enrollment, Department, Course, \
                    CourseAssignment, CourseBySection, Section, MarkEntry, VoucherItem
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Student)
admin.site.register(Instructor)
admin.site.register(Semester)
admin.site.register(Department)
admin.site.register(Course)
admin.site.register(CourseAssignment)
admin.site.register(CourseBySection)
admin.site.register(Section)
admin.site.register(MarkEntry)
admin.site.register(VoucherItem)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student_username','course_name','enrollment_semester')
    list_select_related = ('student__user','course_by_section','semester')