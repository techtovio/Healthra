from django.urls import path
from . import views


app_name = 'insurance'

urlpatterns = [
    path('plans/', views.select_plan, name='select-plan'),
    path('plans/enroll/<int:plan_id>/', views.enroll_plan, name='enroll-plan'),
    path('payment/<int:insurance_id>/', views.process_payment, name='process-insurance-payment'),
    path('dashboard/', views.insurance_dashboard, name='insurance-dashboard'),
    
]