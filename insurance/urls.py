from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('plans/', views.select_plan, name='select-plan'),
    path('plans/enroll/<int:plan_id>/', views.enroll_plan, name='enroll-plan'),
    path('payment/<int:insurance_id>/', views.process_payment, name='process-insurance-payment'),
    path('dashboard/', views.insurance_dashboard, name='insurance-dashboard'),
    #path('generate-receipt/<int:tx_id>/', views.generate_receipt, name='generate-receipt'),
    #path('generate-insurance-receipt/<int:insurance_id>/', views.generate_insurance_receipt, name='generate-insurance-receipt'),
]