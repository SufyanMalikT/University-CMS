from django.db import models
from django.core.exceptions import ValidationError
import uuid
from django.utils import timezone

# Create your models here.

class FeeVoucher(models.Model):
    voucher_type = (
        ('semester_fee','Semester Fee'),
        ('credit_purchase','credit_purchase'),
        ('fines/arrears','Fines/Arrears')
    )
    status_choices = (
        ('pending','Pending'),
        ('paid','Paid'),
        ('unpaid','Unpaid'),
        ('expired','Expired')
    )

    voucher_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    student = models.ForeignKey('accounts.Student', related_name='fee_vouchers', on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount in cents")
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    breakdown = models.JSONField(help_text="Format: {'Tuition': 500, 'Lab': 100}")
    description = models.TextField(blank=True)
    
    semester = models.ForeignKey('academics.Semester', related_name='fee_vouchers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()

    status = models.CharField(max_length=20, choices=status_choices, default='unpaid')
    stripe_payment_intent = models.CharField(max_length=255, null=True, blank=True)

    def clean(self):
        super().clean()

        if self.due_date and self.due_date < timezone.now().date():
            raise ValidationError("Due date cannot be in the past")
        
    def save(self, *args, **kwargs):
        if not self.voucher_id:
            self.voucher_id = f"VCH-{uuid.uuid4().hex[:8].upper()}"

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def tution_fee(self):
        return self.breakdown['total_course_fees']
    
    @property
    def misc_fee(self):
        return self.breakdown['fixed_fees']['exam_fee']+self.breakdown['fixed_fees']['library_fee']
    
    @property
    def registration_fee(self):
        return self.breakdown['fixed_fees']['registraton']
    @property
    def total_amount(self):
        return (self.amount + self.fine_amount) /100
    
    def total_ammount_in_cents(self):
        return int(self.total_amount*100)
    
    def __str__(self):
        return f"Voucher {self.voucher_id} - {self.student.user.username}"

class VoucherItem(models.Model):
    student = models.ForeignKey('accounts.Student', related_name='cart_items', on_delete=models.CASCADE)
    course_by_section = models.ForeignKey('academics.CourseBySection' ,related_name='voucher_items', on_delete=models.CASCADE)
    fee_voucher = models.ForeignKey(FeeVoucher, related_name='voucher_items',on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('fee_voucher','course_by_section','student')

    def __str__(self):
        return f"{self.student.user.username} - {self.course_by_section.course.name}"
    

class FeeConfiguration(models.Model):
    fee_types = (
        ('per_credit','Price of Credit Hour'),
        ('registration','Semester Registration'),
        ('exam_fee','Examination Fee'),
        ('library_fee','Library Charges'),
    )
    name = models.CharField(max_length=30, choices=fee_types, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - ${self.amount}"
    

class Payment(models.Model):
    student = models.ForeignKey('accounts.Student', related_name='payments', on_delete=models.CASCADE)
    voucher = models.OneToOneField(FeeVoucher, related_name='voucher', on_delete=models.CASCADE)
    stripe_charge_id = models.CharField(max_length=120)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Success')

    def __str__(self):
        return f"{self.student.user.get_full_name()} - ${self.amount_paid}"
    

class Ledger(models.Model):
    transaction_types_choices = (
        ('charge','Charge (Enrollment)'),
        ('payment','Payment (Stripe)'),
        ('refund','Refund (Drop)'),
        ('service','Service/Other Charge'),
        ('fine','Late Fine/Penalty')
    )
    student = models.ForeignKey('accounts.Student', related_name='ledger_entries',on_delete=models.CASCADE)
    enrollment = models.ForeignKey('academics.Enrollment', null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20,choices=transaction_types_choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    payment_reference = models.ForeignKey(Payment, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.user.get_full_name()} amount:{self.amount}"