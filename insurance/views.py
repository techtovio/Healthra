from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import InsurancePlan, UserInsurance, InsurancePayment
from wallet.models import UserWallet
from decimal import Decimal
from account.models import Profile, Transaction
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
#from weasyprint import HTML
from wallet.contracts import token

def home(request):
    return render(request, 'index.html')

def buy_hlt(request):
    if request.method == 'POST':
        amount = int(request.POST.get('amount'))
        # Implement your HLT purchase logic here
        # This would involve:
        # 1. Calculating cost in fiat or HBAR
        # 2. Processing payment
        # 3. Minting/sending HLT tokens
        # 4. Recording transaction
        hlt_price_in_usd = 0.1
        
        Transaction.objects.create(
            user=request.user,
            transaction_type='HLT_PURCHASE',
            currency='USD',
            amount=amount * hlt_price_in_usd,
            status='COMPLETED'
        )
        
        messages.success(request, f'Successfully purchased {amount} HLT tokens!')
        return redirect('insurance-dashboard')

def fiat_deposit(request):
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))
        method = request.POST.get('method')
        
        # Process fiat deposit (would integrate with payment processor)
        # Convert to HBAR based on current rate
        
        Transaction.objects.create(
            user=request.user,
            transaction_type='FIAT_DEPOSIT',
            currency='USD',
            amount=amount,
            status='COMPLETED'
        )
        
        messages.success(request, f'Successfully deposited ${amount:.2f}')
        return redirect('insurance-dashboard')
'''def generate_receipt(request, tx_id):
    transaction = Transaction.objects.get(id=tx_id, user=request.user)
    
    # Generate PDF receipt
    html_string = render_to_string('receipts/transaction_receipt.html', {
        'transaction': transaction,
        'user': request.user
    })
    
    html = HTML(string=html_string)
    result = html.write_pdf()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=receipt_{tx_id}.pdf'
    response.write(result)
    
    return response

def generate_insurance_receipt(request, insurance_id):
    insurance = UserInsurance.objects.get(id=insurance_id, user=request.user)
    
    if request.method == 'POST':
        receipt_type = request.POST.get('receipt_type')
        notes = request.POST.get('notes', '')
        
        if receipt_type == 'pdf':
            html_string = render_to_string('receipts/insurance_receipt.html', {
                'insurance': insurance,
                'user': request.user,
                'notes': notes
            })
            
            html = HTML(string=html_string)
            result = html.write_pdf()
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=insurance_receipt_{insurance_id}.pdf'
            response.write(result)
            return response
            
        elif receipt_type == 'email':
            # Implement email sending logic
            pass
            
        return redirect('insurance-dashboard')
   '
   ''' 
@login_required
def select_plan(request):
    plans = InsurancePlan.objects.filter(is_active=True)
    context = {
        'plans': plans,
        'user_has_active_insurance': UserInsurance.objects.filter(
            user=request.user,
            status='ACTIVE'
        ).exists()
    }
    return render(request, 'insurance/select_plan.html', context)

@login_required
def enroll_plan(request, plan_id):
    plan = get_object_or_404(InsurancePlan, id=plan_id)
    wallet = get_object_or_404(UserWallet, user=request.user)
    
    if request.method == 'POST':
        payment_frequency = request.POST.get('payment_frequency', 'MONTHLY')
        
        # Calculate costs
        if payment_frequency == 'ANNUAL':
            hbar_cost = plan.monthly_cost_hbar * Decimal('12') * (1 - plan.annual_discount/100)
            coverage_days = 365
        else:
            hbar_cost = plan.monthly_cost_hbar
            coverage_days = 30
        
        # Create insurance enrollment
        insurance = UserInsurance.objects.create(
            user=request.user,
            plan=plan,
            payment_frequency=payment_frequency,
            status='PENDING',
            hbar_cost=hbar_cost
        )
        
        # Redirect to payment processing
        return redirect('process-insurance-payment', insurance_id=insurance.id)
    
    return render(request, 'insurance/enroll_plan.html', {
        'plan': plan,
        'wallet': wallet,
        'annual_savings': plan.monthly_cost_hbar * Decimal('12') * plan.annual_discount/100
    })

@login_required
def process_payment(request, insurance_id):
    insurance = get_object_or_404(UserInsurance, id=insurance_id, user=request.user)
    
    # In a real implementation, this would interact with Hedera
    # For now, we'll simulate successful payment
    today = timezone.now().date()
    
    if insurance.payment_frequency == 'ANNUAL':
        coverage_end = today + timedelta(days=365)
    else:
        coverage_end = today + timedelta(days=30)
    
    # Update insurance status
    insurance.status = 'ACTIVE'
    insurance.start_date = today
    insurance.end_date = coverage_end
    insurance.next_payment_date = coverage_end
    insurance.save()
    
    # Record payment (in reality, this would come from Hedera transaction)
    InsurancePayment.objects.create(
        insurance=insurance,
        transaction_id=f"SIMULATED_{timezone.now().timestamp()}",
        amount_hbar=insurance.hbar_cost,
        coverage_period_start=today,
        coverage_period_end=coverage_end,
        is_successful=True
    )
    
    messages.success(request, "Insurance payment processed successfully!")
    return redirect('insurance-dashboard')

@login_required
def insurance_dashboard(request):
    active_insurance = UserInsurance.objects.filter(
        user=request.user,
        status='ACTIVE'
    ).first()
    
    payment_history = InsurancePayment.objects.filter(
        insurance__user=request.user
    ).order_by('-payment_date')[:5]
    
    return render(request, 'insurance/dashboard.html', {
        'active_insurance': active_insurance,
        'payment_history': payment_history
    })