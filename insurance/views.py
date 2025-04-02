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
from wallet.views import transfer_tokens
from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TransferTransaction,
    Network,
    TokenAssociateTransaction,
    TokenId,
    TopicId,
    TopicCreateTransaction,
    TopicMessageSubmitTransaction,
)
from wallet.contracts import mirror_node
from django.http import HttpResponseRedirect
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
def home(request):
    return render(request, 'index.html')


def create_topic():
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))

    client.set_operator(operator_id, operator_key)

    transaction = (
        TopicCreateTransaction(
            memo="Healthra Insurance",
            admin_key=operator_key.public_key()
        )
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        if receipt and receipt.topicId:
            print(f"Topic created with ID: {receipt.topicId}")
            return receipt.topicId
        else:
            print("Topic creation failed: Topic ID not returned in receipt.")
    except Exception as e:
        print(f"Topic creation failed: {str(e)}")

def submit_message(message):
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    topic_id = TopicId.from_string(os.getenv('TOPIC_ID'))

    client.set_operator(operator_id, operator_key)

    transaction = (
        TopicMessageSubmitTransaction(topic_id=topic_id, message=message)
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        print(f"Message submitted to topic {topic_id}: {message}")
        return True
    except Exception as e:
        print(f"Message submission failed: {str(e)}")
        return False


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
    
    today = timezone.now().date()
    
    if insurance.payment_frequency == 'ANNUAL':
        coverage_end = today + timedelta(days=365)
    else:
        coverage_end = today + timedelta(days=30)
    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    poolId=AccountId.from_string(os.getenv('HEALHRA_POOL_ID'))
    token_id = os.getenv('Token_ID')
    # Transfer HLT and Submit HCL-10 HEALHRA_POOL_ID
    wallet = UserWallet.objects.get(user=request.user)
    recipient_id = wallet.recipient_id
    recipient_key = wallet.decrypt_key().split("hex=")[-1].strip(">")
    balance = mirror_node.get_token_balance_for_account(account_id=recipient_id, token_id=token_id)
    if balance >= insurance.hbar_cost:
        transfer = transfer_tokens(operator_id_sender=AccountId.from_string(recipient_id), operator_key_sender=PrivateKey.from_string(recipient_key), recipient_id=poolId, amount=int(insurance.hbar_cost))
        if transfer == True:
            message = {
                "type": "insurance_payment",
                "insurance_id": insurance_id,
                "amount": insurance.hbar_cost,
                "timestamp": datetime.now().isoformat()
            }
            submit_message(message=str(message))
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
        else:
            messages.warning(request, 'We are unable to process your request now, please try again later!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        messages.warning(request, f"You don't have sufficient HLT to select this plan, your HLT Balance is {balance}, buy HLT and try again")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
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