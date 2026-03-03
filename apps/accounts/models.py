from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum

# Create your models here.

class CustomUser(AbstractUser):
    phone = models.CharField(max_length=30,unique=True,null=True, blank=True)
    birth_date = models.DateField(null=True,blank=True)

    @property
    def is_student(self):
        return hasattr(self, 'student_profile')
    
    @property    
    def is_instructor(self):
        return hasattr(self, 'instructor_profile')

        
    def clean(self):
        super().clean()
        if  self.birth_date:
            if self.birth_date > timezone.now().date():
                raise ValidationError({
                    'birth_date':'Birthdate is invalid'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
    

class Student(models.Model):
    user = models.OneToOneField(CustomUser,related_name='student_profile',on_delete=models.CASCADE)

    
    @property
    def used_credit_hours(self):
        return self.enrollments.aggregate(
            total=Sum('course_by_section__course__credit_hours')
        )['total'] or 0

    @property
    def available_credit_hours(self):
        return self.total_credit_hours - self.used_credit_hours
    

    def used_credits_for_semester(self, semester):
        return self.enrollments.filter(semester=semester) \
            .aggregate(total=Sum('course_by_section__course__credit_hours'))['total'] or 0
    


    def calculate_cgpa(self):
        # Use select_related to avoid hitting the database inside the loop (N+1 problem)
        enrollments = self.enrollments.select_related('course_by_section__course').all()
        
        if not enrollments:
            return 0.0

        grade_points_sum = 0
        credit_hour_sum = 0
        
        for enrollment in enrollments:
            # Use our new percentage property
            score = enrollment.percentage
            credits = enrollment.course_by_section.course.credit_hours
            
            # Determine weight based on percentage
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
                
            grade_points_sum += (weight * credits)
            credit_hour_sum += credits

        # Prevent crash if student is enrolled in 0 credit hours
        if credit_hour_sum == 0:
            return 0.0
            
        return round(grade_points_sum / credit_hour_sum, 2)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Instructor(models.Model): 
    user = models.OneToOneField(CustomUser,related_name='instructor_profile',on_delete=models.CASCADE)
    department = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"