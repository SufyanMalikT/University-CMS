from django.db import models
from django.contrib.auth.models import AbstractUser 
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Avg, Sum, Count, Q
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
# Create your models here.


class Building(models.Model):
    name = models.CharField(max_length=30)
    location = models.CharField(max_length=180)

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=55)
    created_at = models.DateTimeField(auto_now_add=True)
    building = models.ForeignKey(Building, related_name='departments', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.building}"
    
class Room(models.Model):
    room_choices = (
        ('lab','Lab'),
        ('classroom','Classroom'),
        ('office','Office'),
    )
    name = models.CharField(max_length=10)
    department = models.ForeignKey(Department, related_name='rooms', on_delete=models.CASCADE)
    room_type = models.CharField(max_length=15, choices=room_choices, default='classroom')

    def __str__(self):
        return f"{self.room_type} - {self.name}"


class Course(models.Model):
    course_type_choices = (
        ('Lab','Lab'),
        ('Theory','Theory')
    )
    name = models.CharField(max_length=55)
    credit_hours = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    course_code = models.CharField(max_length=10,unique=True)
    course_type = models.CharField(max_length=10, choices=course_type_choices, default='Theory')


    def __str__(self):
        return f"{self.name} - {self.credit_hours}"



class Semester(models.Model):
    session_choices = (
        ('Fall','Fall'),
        ('Spring','Spring')
    )
    session = models.CharField(max_length=30, choices=session_choices)
    start_date = models.DateField()
    end_date = models.DateField()

    add_course_deadline = models.DateField(null=True, blank=True)
    drop_course_deadline = models.DateField(null=True, blank=True)
    fee_payment_deadline = models.DateField(null=True, blank=True)
    voucher_validity_days = models.PositiveSmallIntegerField(default=7)
    max_credit_hours = models.PositiveSmallIntegerField(null=True, blank=True)

    @property
    def get_sem(self):
        return f"{self.session} {self.start_date.year}"
    
    @property
    def can_add_course(self):
        if not self.add_course_deadline:
            return True
        elif timezone.now().date() > self.add_course_deadline:
            return False
        else:
            return True
    
    @property
    def can_drop_course(self):
        if not self.drop_course_deadline:
            return True
        elif timezone.now().date() > self.drop_course_deadline:
            return False
        else:
            return True
        
    @classmethod
    def latest_semester(cls):
        return cls.objects.latest('end_date')
    
    @property
    def is_past_deadline(self):
        if self.fee_payment_deadline:
            return timezone.now().date() > self.fee_payment_deadline
        return False

    @property
    def active_enrollments(self):
        return self.enrollments.filter(status='active')
    def clean(self):
        super().clean()

        if self.start_date > self.end_date:
            raise ValidationError("Start date cannot be after end date.")

        if self.add_course_deadline and not (self.start_date <= self.add_course_deadline <= self.end_date):
            raise ValidationError("Add deadline must be within semester dates.")

        if self.drop_course_deadline and not (self.start_date <= self.drop_course_deadline <= self.end_date):
            raise ValidationError("Drop deadline must be within semester dates.")

        if self.add_course_deadline and self.drop_course_deadline:
            if self.add_course_deadline > self.drop_course_deadline:
                raise ValidationError("Add deadline cannot be after drop deadline.")

    def save(self,*args,**kwargs):
        self.full_clean()
        super().save(*args,**kwargs)

    def __str__(self):
        return self.get_sem







class Section(models.Model):
    department = models.ForeignKey(Department, related_name='sections', on_delete=models.CASCADE)
    section_id = models.CharField(max_length=25,unique=True)
    limit_of_students = models.PositiveSmallIntegerField(default=50)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.section_id
    


class CourseBySection(models.Model):
    course = models.ForeignKey(Course, related_name='sections',on_delete=models.CASCADE)
    section = models.ForeignKey(Section, related_name='courses', on_delete=models.CASCADE)
    course_code_by_section = models.PositiveSmallIntegerField()
    created_at = models.DateField(auto_now_add=True)
    no_of_enrolled_students = models.PositiveSmallIntegerField(default=0)

    @property 
    def available_seats(self):
        pending_seats = self.voucher_items.filter(
            fee_voucher__status='unpaid',
            fee_voucher__due_date__gte = timezone.now().today()
        ).count()

        return self.section.limit_of_students - (self.no_of_enrolled_students + pending_seats)
    
    def clean(self):
        super().clean()

        if self.no_of_enrolled_students > self.section.limit_of_students:
            raise ValidationError("No more seats available for this section")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('course','section')
    def __str__(self):
        return f"{self.course.name} - {self.section.section_id} - {self.course_code_by_section}"
    


class CourseAssignment(models.Model):
    course_by_section = models.ForeignKey(CourseBySection, related_name='assignments',on_delete=models.CASCADE)
    instructor = models.ForeignKey('accounts.Instructor', related_name='assignments',on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, related_name='assignments', on_delete=models.CASCADE)
    assigned_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('course_by_section','instructor','semester')

    def __str__(self):
        return f"{self.course_by_section.course.name} is assigned to {self.instructor.user.first_name} {self.instructor.user.last_name} for {self.semester.get_sem}"
    


class Enrollment(models.Model):
    status_choices = (
        ('active','Active'),
        ('dropped','Dropped (Before Deadline)'),
        ('withdrawn','Withdrawn (After Deadline)'),
    )
    student = models.ForeignKey('accounts.Student',related_name='enrollments',on_delete=models.CASCADE)
    course_by_section = models.ForeignKey(CourseBySection,related_name='enrollments',on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, related_name='enrollments',on_delete=models.CASCADE)
    enrolled_at = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=status_choices, default='active')
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2)
    exam_fee = models.DecimalField(max_digits=10, decimal_places=2)
    @property
    def student_username(self):
        return self.student.user.username
    
    @property
    def course_name(self):
        return self.course_by_section.course.name
    
    @property
    def enrollment_semester(self):
        return f"{self.semester.session} {self.semester.start_date.year}"
    
    @property
    def total_marks(self):
        return self.marks.aggregate(Total=Sum('obtained_marks'))['Total'] or 0
    
    @property
    def is_cleared(self):
        if self.percentage >= 50:
            return True
        else:
            return False
        
    @property
    def percentage(self):
        data = self.marks.filter(is_locked=True).aggregate(
            obtained=Sum('obtained_marks'),
            total=Sum('total_marks')
        )
        obtained = data['obtained'] or 0
        total = data['total'] or 0
        
        if total > 0:
            return (obtained / total) * 100
        return 0

    @property
    def course_obtained_marks(self):
        return self.marks.aggregate(Total=Sum('obtained_marks'))['Total'] or 0
    
    @property
    def course_total_marks(self):
        return self.marks.aggregate(Total=Sum('total_marks'))['Total'] or 0
    
    @property
    def grade(self):
        score = self.percentage
        if score > 90:
            grade = "A"
        elif score >= 80:
            grade = "A-"
        elif score >= 75:
            grade = "B+"
        elif score >= 70:
            grade = "B"
        elif score >= 64:
            grade = "B-"
        elif score >= 60: 
            grade = "C+"
        elif score >= 58:
            grade  = "C"
        elif score >= 54:
            grade = "C-"
        elif score >= 50:
            grade = "D"
        else:
            grade = "F"
        return grade
    
    @property
    def gpa(self):
        score = self.percentage
        if score > 90:
            grade = 4.0
        elif score >= 80:
            grade = 3.66
        elif score >= 75:
            grade = 3.33
        elif score >= 70:
            grade = 3.0
        elif score >= 64:
            grade = 2.8
        elif score >= 60: 
            grade = 2.5
        elif score >= 58:
            grade  = 2.3
        elif score >= 54:
            grade = 2.1
        elif score >= 50:
            grade = 2.0
        else:
            grade = 0.0 
        return grade

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course_by_section','semester'], 
                condition=Q(status='active'),
                name='unique_active_enrollment'
            )
        ]
    
    def clean(self):
        super().clean()

        if (self.semester.max_credit_hours 
            and self.student.used_credits_for_semester(self.semester) 
            + self.course_by_section.course.credit_hours 
            > self.semester.max_credit_hours):
            raise ValidationError('Max limit of credit hours breached for this semesters enrollment')
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.user.username} is enrolled in {self.course_by_section.course.name}"
    
class MarkEntry(models.Model):
    theory_category_choices = (
        ('Assignment','Assignment'),
        ('Participation','Participation'),
        ('Presentation','Presentation'),
        ('Project','Project'),
        ('Midterm','Midterm'),
        ('Finalterm','Finalterm'),
    )
    lab_category_choices = (
        ('LabExam','LabExam'),
        ('LabAtt','LabAtt'),
        ('LabViva','LabViva'),
        ('LabManual','LabManual'),
    )

    all_category_choices = theory_category_choices + lab_category_choices

    enrollment = models.ForeignKey(Enrollment, related_name='marks', on_delete=models.CASCADE)
    category = models.CharField(max_length=20,choices=all_category_choices)
    title = models.CharField(max_length=30)
    obtained_marks = models.DecimalField(max_digits=5, decimal_places=2)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)

    def clean(self):
        if self.pk:
            original_entry = MarkEntry.objects.get(pk=self.pk)
            if original_entry.is_locked:
                raise ValidationError("This mark entry is locked, it cannot be modified")
        super().clean()

        theory_keys = [choice[0] for choice in self.theory_category_choices]
        lab_keys = [choice[0] for choice in self.lab_category_choices]

        if self.enrollment.course_by_section.course.course_type == 'Theory' and self.category in lab_keys:
            raise ValidationError("Cannot choose a category for lab courses for a theory course")
        
        if self.enrollment.course_by_section.course.course_type == 'Lab' and self.category in theory_keys:
            raise ValidationError("Cannot choose a category for theory courses for a lab course")
        
        if self.total_marks < self.obtained_marks:
            raise ValidationError("Obtained marks can\'t be greater than total marks")
        
        if self.total_marks is not None and self.obtained_marks is not None:
            if self.obtained_marks > self.total_marks:
                raise ValidationError(f"Score ({self.obtained_marks}) cannot exceed the total possible marks ({self.total_marks}).")
            
            if self.total_marks <= 0:
                raise ValidationError("Total marks for an entry must be greater than zero.")
    

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('enrollment','category')

    def __str__(self):
        return f"{self.title} - {self.enrollment.student.user.username}"
    

class ClassSchedule(models.Model):
    weekday_choices = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ) 
    course_by_section = models.ForeignKey(CourseBySection, related_name='schedules', on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, related_name='schedules', on_delete=models.CASCADE)
    day_of_the_week = models.CharField(max_length=20, choices=weekday_choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.start_time > self.end_time:
            raise ValidationError("The class start time cannot be past its end time")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('course_by_section', 'semester','day_of_the_week')
    def __str__(self):
        return f"{self.course_by_section.course.name} from {self.start_time} till {self.end_time}"
    
class ClassSession(models.Model):
    instructor = models.ForeignKey('accounts.Instructor', related_name='class_sessions', on_delete=models.SET_NULL, null=True)
    schedule = models.ForeignKey(ClassSchedule, related_name='sessions',on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()

        if self.date > timezone.now().date():
            raise ValidationError("A session can only be created when it is already occured.")
        
    def save(self, *args , **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.instructor.user.get_full_name()} attended {self.schedule.course_by_section.course.name} on {self.date}"
    
class AttendanceEntry(models.Model):
    session = models.ForeignKey(ClassSession, related_name='attendance', on_delete=models.CASCADE)
    student = models.ForeignKey('accounts.student', related_name='attendance', on_delete=models.CASCADE)
    was_present = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session','student')

    def clean(self):
        super().clean()
        if not self.student.enrollments.filter(status='active',course_by_section=self.session.schedule.course_by_section).exists():
            raise ValidationError("Student is not enrolled this course")
        

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.session.date}"


class DateSheetEntry(models.Model):
    course_by_section = models.OneToOneField(CourseBySection, on_delete=models.CASCADE)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.ForeignKey(Room, related_name='exam_dates', on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['exam_date', 'start_time']
    def __str__(self):
        return f"{self.course_by_section.course.name} - {self.room.name} - {self.exam_date}" 