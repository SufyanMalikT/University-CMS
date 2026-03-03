from django.contrib import admin
from .models import FeeConfiguration, FeeVoucher, VoucherItem, Payment
# Register your models here.

admin.site.register(FeeConfiguration)
admin.site.register(FeeVoucher)
admin.site.register(VoucherItem)
admin.site.register(Payment)