from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import UserWallet, Transaction
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import TransferForm
import os
from dotenv import load_dotenv
from wallet.contracts.hedera import load_operator_credentials, create_new_account, query_balance, transfer_token
from wallet.contracts import mirror_node
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.views.decorators.http import require_GET
import requests
from account.models import Profile
from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TransferTransaction,
    Network,
    TokenAssociateTransaction,
    TokenId,
    TopicMessageQuery
)
from insurance.models import InsurancePayment
from decimal import Decimal
from django.http import HttpResponseRedirect
from django.views import View
from decimal import Decimal
import json
from datetime import datetime, timedelta
import base64


load_dotenv()
def get_insurance_payments(request):
    """Query Hedera Mirror API for insurance payment messages with proper endpoint usage"""
    MIRROR_NODE_URL = "https://testnet.mirrornode.hedera.com"
    TOPIC_ID = "0.0.5811308"  # Replace with your actual topic ID
    LIMIT = 10

    try:
        # First verify the topic exists
        topic_response = requests.get(
            f"{MIRROR_NODE_URL}/api/v1/topics/{TOPIC_ID}",
            headers={'Accept': 'application/json'},
            timeout=5
        )
        
        if topic_response.status_code == 404:
            return JsonResponse({'error': f"Topic {TOPIC_ID} not found"}, status=404)
        
        topic_response.raise_for_status()
        
        # Get messages from the topic
        messages_response = requests.get(
            f"{MIRROR_NODE_URL}/api/v1/topics/{TOPIC_ID}/messages",
            params={
                "limit": LIMIT,
                "order": "desc"  # Newest messages first
            },
            headers={'Accept': 'application/json'},
            timeout=10
        )
        messages_response.raise_for_status()

        messages = []
        for msg in messages_response.json().get('messages', []):
            try:
                if not msg.get('message'):
                    continue

                # Decode and parse message content
                content = base64.b64decode(msg['message']).decode('utf-8')
                message_data = json.loads(content)

                # Only process insurance payments
                if message_data.get('type') != 'insurance_payment':
                    continue

                # Format the timestamp
                consensus_ts = msg['consensus_timestamp']
                try:
                    dt = datetime.strptime(consensus_ts.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    formatted_date = dt.strftime("%b %d, %Y %H:%M:%S")
                except:
                    formatted_date = consensus_ts

                messages.append({
                    'sequence_number': msg['sequence_number'],
                    'insurance_id': message_data.get('insurance_id'),
                    'amount': float(message_data.get('amount', 0)),
                    'timestamp': consensus_ts,
                    'formatted_date': formatted_date,
                    'running_hash': msg.get('running_hash')
                })

            except (KeyError, ValueError, json.JSONDecodeError) as e:
                continue

        return JsonResponse({
            'topic_info': {
                'topic_id': TOPIC_ID,
                'memo': topic_response.json().get('memo', ''),
                'created_timestamp': topic_response.json().get('created_timestamp')
            },
            'payments': messages
        })

    except requests.RequestException as e:
        error_msg = f"Mirror node API error: {str(e)}"
        if hasattr(e, 'response'):
            try:
                error_details = e.response.json()
                error_msg += f" - {error_details.get('_status', {}).get('messages', [''])[0]}"
            except:
                error_msg += f" (Status: {e.response.status_code})"
        return JsonResponse({'error': error_msg}, status=500)

@login_required
def wallet_history(request):
    transactions = mirror_node.get_token_transactions(account_id=request.user.wallet.recipient_id, token_id=os.getenv('Token_ID'))
    print(transactions)
    return JsonResponse(transactions)

@login_required
def wallet_details(request):
    wallet = get_object_or_404(UserWallet, user=request.user)
    qpt_balance = mirror_node.get_token_balance_for_account(account_id=wallet.recipient_id, token_id=os.getenv('Token_ID'))
    context = {
        'qpt_public_key': wallet.qpt_public_key.split("hex=")[-1].strip(">"),
        'recipient_id': wallet.recipient_id,
        'qpt_balance': qpt_balance,
    }
    return render(request, 'wallet/wallet_details.html', context)

@login_required
def wallet_balance(request):
    user = request.user
    wallet = UserWallet.objects.get(user=user)
    network_type = os.getenv('NETWORK')
    token_id = os.getenv('Token_ID')
    balance = mirror_node.get_token_balance_for_account(account_id=wallet.recipient_id, token_id=token_id)
    print(balance)
    data = {
        'hlt_balance':balance
    }
    return JsonResponse(data)


@login_required
def transaction_history(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(transactions, 10)  # Show 10 transactions per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    data = [
        {
            'transaction_type': txn.transaction_type,
            'currency': txn.currency,
            'amount': txn.amount,
            'recipient_id': txn.recipient_id,
            'status': txn.status,
            'created_at': txn.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for txn in page_obj
    ]
    return JsonResponse({'transactions': data})

def associate_token(recipient_id_new, recipient_key_new):
    network = Network(network='testnet')
    client = Client(network)

    recipient_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    recipient_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    token_id = TokenId.from_string(os.getenv('Token_ID'))  # Update as needed
    client.set_operator(recipient_id, recipient_key)

    transaction = (
        TokenAssociateTransaction()
        .set_account_id(recipient_id_new)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(recipient_key_new)
    )

    try:
        receipt = transaction.execute(client)
        print("Token association successful.")
    except Exception as e:
        print(f"Token association failed: {str(e)}")

def create_pool_wallets(request):
    operator_id, operator_key = load_operator_credentials()

    network_type = os.getenv('NETWORK')
    token_id = os.getenv('Token_ID')
    network = Network(network=network_type)
    client = Client(network)
    client.set_operator(operator_id, operator_key)
    name = 'Healthra Pool'
    recipient_id, recipient_private_key, new_account_public_key = create_new_account(name, client)
    print(recipient_id)
    print(recipient_private_key)
    associate_token(recipient_id, recipient_private_key)
    return JsonResponse({'status':'success'})

def transfer_tokens(operator_id_sender, operator_key_sender, recipient_id, amount):
    network_type = os.getenv('NETWORK')
    network = Network(network=network_type)
    client = Client(network)
    print(amount)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    token_id = TokenId.from_string(os.getenv('Token_ID'))

    client.set_operator(operator_id, operator_key)

    transaction = (
        TransferTransaction()
        .add_token_transfer(token_id, operator_id_sender, -amount)
        .add_token_transfer(token_id, recipient_id, amount)
        .freeze_with(client)
        .sign(operator_key_sender)
    )

    try:
        receipt = transaction.execute(client)
        print("Token transfer successful.")
        return True
    except Exception as e:
        print(f"Token transfer failed: {str(e)}")
        return False

def fund_claim(request):
    clubs = InsurancePayment.objects.all()#ADMIN_KEY
    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    for club in clubs:
        recipient_id = AccountId.from_string(club.hospital_id)
        transfer_tokens(operator_id_sender=operator_id, operator_key_sender=operator_key, recipient_id=recipient_id, amount=1000)
    return render(request, 'contracts/assign_user_wallet.html')

def buy_hlt(request):
    if request.method == 'POST':
        amount = request.POST['fiat_amount']
        f_amount = float(amount)
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        recipient_id = AccountId.from_string(request.user.wallet.recipient_id)
        print(float(request.user.profile.funds))
        print(float(request.user.profile.funds) > float(f_amount*100))
        if float(request.user.profile.funds) >= float(f_amount*100):
            buy = transfer_tokens(operator_id_sender=operator_id, operator_key_sender=operator_key, recipient_id=recipient_id, amount=int(amount))
            if buy == True:
                profile = Profile.objects.get(user=request.user)
                profile.funds -= Decimal(f_amount*100)
                profile.save()
                messages.success(request, f'HLT Purchase was successful, {amount} HLT has been transfered to your wallet')
            else:
                messages.warning(request, 'An error occured while trying to purchase HLT, please try again.')
        else:
            messages.warning(request, f"You don't have sufficient funds to purchase {amount} HLT, please add funds and try again.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


TESTNET_MIRROR_URL = os.getenv('MIRROR_URL')#"https://testnet.mirrornode.hedera.com/api/v1"

@never_cache
def token_info(request):
    token_id = os.getenv('Token_ID')
    url = f"https://testnet.mirrornode.hedera.com/api/v1/tokens/{token_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        return JsonResponse({
            'status': 'success',
            'name': data.get('name', 'Unknown'),
            'symbol': data.get('symbol', 'UNK'),
            'total_supply': int(data.get('total_supply', 0)),
            'decimals': int(data.get('decimals', 0)),
            'token_id': token_id,
            'timestamp': response.headers.get('Date', '')
        })
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_GET
def token_holders(request):
    token_id = os.getenv('Token_ID')
    if not token_id:
        return JsonResponse({
            'status': 'error',
            'message': 'Token_ID not configured'
        }, status=500)

    try:
        # Get page number from request (default to 1)
        page = int(request.GET.get('page', 1))
        per_page = 10  # Show 10 holders per page
        
        # Get all holders from mirror node
        response = requests.get(
            f"https://testnet.mirrornode.hedera.com/api/v1/tokens/{token_id}/balances",
            params={'limit': 100},  # Get top 100 holders
            timeout=5
        )
        response.raise_for_status()
        
        holders_data = response.json().get('balances', [])
        
        # Process and sort holders
        all_holders = sorted(
            [
                {
                    'account': holder['account'],
                    'balance': int(holder['balance'])
                }
                for holder in holders_data
                if int(holder['balance']) > 0
            ],
            key=lambda x: -x['balance']  # Sort by balance descending
        )
        
        # Calculate pagination
        total_holders = len(all_holders)
        total_pages = (total_holders + per_page - 1) // per_page
        start_index = (page - 1) * per_page
        paginated_holders = all_holders[start_index:start_index + per_page]
        
        return JsonResponse({
            'status': 'success',
            'holders': paginated_holders,
            'total_circulating': sum(h['balance'] for h in all_holders),
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_holders': total_holders,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)