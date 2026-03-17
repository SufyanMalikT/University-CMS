from django.contrib import admin
from .models import  Semester, Enrollment, Department, Course, \
                    CourseAssignment, CourseBySection, Section, MarkEntry, Building, Room
# Register your models here.

admin.site.register(Semester)
admin.site.register(Department)
admin.site.register(Course)
admin.site.register(CourseAssignment)
admin.site.register(CourseBySection)
admin.site.register(Section)
admin.site.register(MarkEntry)
admin.site.register(Building)
admin.site.register(Room)



@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student_username','course_name','enrollment_semester')
    list_select_related = ('student__user','course_by_section','semester')