from django.contrib import admin

# Register your models here.
from insurance.models import InsurancePayment, InsurancePlan, UserInsurance
admin.site.register(InsurancePayment)
admin.site.register(UserInsurance)
admin.site.register(InsurancePlan)