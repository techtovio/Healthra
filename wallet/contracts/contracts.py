import os
from dotenv import load_dotenv
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_dissociate_transaction import TokenDissociateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.consensus.topic_update_transaction import TopicUpdateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery

load_dotenv()

class HederaService:
    _client = None
    
    @classmethod
    def get_client(cls):
        """Initialize and return a singleton Hedera client"""
        if cls._client is None:
            operator_id, operator_key = cls._load_operator_credentials()
            network = Network(network=os.getenv('NETWORK', 'testnet'))
            cls._client = Client(network)
            cls._client.set_operator(operator_id, operator_key)
        return cls._client

    @staticmethod
    def _load_operator_credentials():
        """Load operator credentials from environment variables"""
        try:
            operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
            operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
            return operator_id, operator_key
        except Exception as e:
            raise ValueError(f"Error parsing operator credentials: {e}")

    # Account Management
    @staticmethod
    def create_account(initial_balance=100000000):
        """Create a new Hedera account"""
        client = HederaService.get_client()
        new_key = PrivateKey.generate()
        
        try:
            transaction = AccountCreateTransaction(
                key=new_key.public_key(),
                initial_balance=initial_balance
            ).freeze_with(client).sign(client.operator_private_key)

            receipt = transaction.execute(client)
            if not receipt.accountId:
                raise ValueError("AccountID not found in receipt")
            
            return {
                'account_id': receipt.accountId,
                'private_key': new_key.to_string(),
                'public_key': new_key.public_key().to_string()
            }
        except Exception as e:
            raise ValueError(f"Account creation failed: {str(e)}")

    @staticmethod
    def get_balance(account_id):
        """Query account balance"""
        try:
            return CryptoGetAccountBalanceQuery(
                account_id=account_id
            ).execute(HederaService.get_client())
        except Exception as e:
            raise ValueError(f"Balance query failed: {str(e)}")

    # Token Management
    @staticmethod
    def create_token(token_name, token_symbol, treasury_id=None, **kwargs):
        """Create a new token with configurable parameters"""
        client = HederaService.get_client()
        treasury_id = treasury_id or client.operator_account_id
        
        try:
            transaction = TokenCreateTransaction(
                token_name=token_name,
                token_symbol=token_symbol,
                treasury_account_id=treasury_id,
                **kwargs
            ).freeze_with(client).sign(client.operator_private_key)

            if kwargs.get('admin_key'):
                transaction.sign(kwargs['admin_key'])

            receipt = transaction.execute(client)
            if not receipt.tokenId:
                raise ValueError("Token ID not returned in receipt")
            
            return receipt.tokenId
        except Exception as e:
            raise ValueError(f"Token creation failed: {str(e)}")

    @staticmethod
    def associate_token(account_id, private_key_str, token_id):
        """
        Associate a single token with an account
        Args:
            account_id (str): Account ID in 0.0.123 format
            private_key_str (str): Private key as string
            token_id (str): Token ID in 0.0.123 format
        Returns:
            dict: {
                'success': bool,
                'transaction_id': str,
                'receipt': dict,
                'error': str (if any)
            }
        """
        client = HederaService.get_client()
        
        try:
            # Convert inputs to proper objects
            account = AccountId.from_string(account_id)
            token = AccountId.from_string(token_id)  # TokenID inherits from AccountId
            private_key = PrivateKey.from_string(private_key_str)
            
            transaction = (
                TokenAssociateTransaction()
                .set_account_id(account)
                .set_token_ids([token])
                .freeze_with(client)
                .sign(private_key)
            )
            
            # Execute and wait for receipt
            response = transaction.execute(client)
            receipt = response.get_receipt(client)
            
            return {
                'success': True,
                'transaction_id': response.transactionId.toString(),
                'receipt': {
                    'status': ResponseCode.get_name(receipt.status),
                    'account_id': str(account),
                    'token_id': str(token)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'account_id': account_id,
                'token_id': token_id
            }

    @staticmethod
    def dissociate_tokens(account_id, private_key, token_ids):
        """Dissociate tokens from an account"""
        client = HederaService.get_client()
        
        try:
            transaction = TokenDissociateTransaction(
                account_id=account_id,
                token_ids=token_ids
            ).freeze_with(client).sign(client.operator_private_key)

            if private_key:
                transaction.sign(private_key)

            receipt = transaction.execute(client)
            if receipt.status != ResponseCode.SUCCESS:
                raise ValueError(f"Dissociation failed: {ResponseCode.get_name(receipt.status)}")
            
            return True
        except Exception as e:
            raise ValueError(f"Token dissociation failed: {str(e)}")

    @staticmethod
    def transfer_tokens(token_id, sender_id, sender_key, recipient_id, amount):
        """Transfer tokens between accounts"""
        client = HederaService.get_client()
        
        try:
            transaction = (
                TransferTransaction()
                .add_token_transfer(token_id, sender_id, -amount)
                .add_token_transfer(token_id, recipient_id, amount)
                .freeze_with(client)
                .sign(sender_key)
            )
            
            receipt = transaction.execute(client)
            if receipt.status != ResponseCode.SUCCESS:
                raise ValueError(f"Transfer failed: {ResponseCode.get_name(receipt.status)}")
            
            return receipt
        except Exception as e:
            raise ValueError(f"Token transfer failed: {str(e)}")

    @staticmethod
    def delete_token(token_id, admin_key):
        """Delete a token"""
        client = HederaService.get_client()
        
        try:
            transaction = TokenDeleteTransaction(
                token_id=token_id
            ).freeze_with(client).sign(client.operator_private_key)

            if admin_key:
                transaction.sign(admin_key)

            receipt = transaction.execute(client)
            if receipt.status != ResponseCode.SUCCESS:
                raise ValueError(f"Deletion failed: {ResponseCode.get_name(receipt.status)}")
            
            return True
        except Exception as e:
            raise ValueError(f"Token deletion failed: {str(e)}")

    @staticmethod
    def freeze_token(token_id, account_id, freeze_key):
        """Freeze token for an account"""
        client = HederaService.get_client()
        
        try:
            transaction = TokenFreezeTransaction(
                token_id=token_id,
                account_id=account_id
            ).freeze_with(client).sign(client.operator_private_key)

            if freeze_key:
                transaction.sign(freeze_key)

            receipt = transaction.execute(client)
            if receipt.status != ResponseCode.SUCCESS:
                raise ValueError(f"Freeze failed: {ResponseCode.get_name(receipt.status)}")
            
            return True
        except Exception as e:
            raise ValueError(f"Token freeze failed: {str(e)}")

    @staticmethod
    def mint_fungible_token(token_id, amount, supply_key):
        """Mint additional fungible tokens"""
        client = HederaService.get_client()
        
        try:
            transaction = TokenMintTransaction(
                token_id=token_id,
                amount=amount
            ).freeze_with(client).sign(client.operator_private_key)

            if supply_key:
                transaction.sign(supply_key)

            receipt = transaction.execute(client)
            if receipt.status != ResponseCode.SUCCESS:
                raise ValueError(f"Minting failed: {ResponseCode.get_name(receipt.status)}")
            
            return receipt.total_supply
        except Exception as e:
            raise ValueError(f"Token minting failed: {str(e)}")

    @staticmethod
    def mint_nft(token_id, metadata, supply_key):
        """Mint non-fungible tokens"""
        client = HederaService.get_client()
        
        try:
            transaction = TokenMintTransaction(
                token_id=token_id,
                metadata=metadata
            ).freeze_with(client).sign(client.operator_private_key)

            if supply_key:
                transaction.sign(supply_key)

            receipt = transaction.execute(client)
            if receipt.status != ResponseCode.SUCCESS:
                raise ValueError(f"NFT minting failed: {ResponseCode.get_name(receipt.status)}")
            
            return receipt.serial_numbers
        except Exception as e:
            raise ValueError(f"NFT minting failed: {str(e)}")

    # Topic Management
    @staticmethod
    def create_topic(memo="", submit_key=None, admin_key=None):
        """Create a new consensus topic"""
        client = HederaService.get_client()
        admin_key = admin_key or client.operator_private_key.public_key()
        
        try:
            transaction = TopicCreateTransaction(
                memo=memo,
                admin_key=admin_key,
                submit_key=submit_key
            ).freeze_with(client).sign(client.operator_private_key)

            receipt = transaction.execute(client)
            if not receipt.topicId:
                raise ValueError("Topic ID not returned in receipt")
            
            return receipt.topicId
        except Exception as e:
            raise ValueError(f"Topic creation failed: {str(e)}")

    @staticmethod
    def submit_topic_message(topic_id, message):
        """Submit message to a topic"""
        client = HederaService.get_client()
        
        try:
            transaction = TopicMessageSubmitTransaction(
                topic_id=topic_id,
                message=message
            ).freeze_with(client).sign(client.operator_private_key)

            receipt = transaction.execute(client)
            if receipt.status != ResponseCode.SUCCESS:
                raise ValueError(f"Message submission failed: {ResponseCode.get_name(receipt.status)}")
            
            return receipt
        except Exception as e:
            raise ValueError(f"Message submission failed: {str(e)}")

    @staticmethod
    def update_topic(topic_id, memo=None, admin_key=None):
        """Update topic properties"""
        client = HederaService.get_client()
        
        try:
            transaction = TopicUpdateTransaction(
                topic_id=topic_id,
                memo=memo if memo else ""
            ).freeze_with(client).sign(client.operator_private_key)

            if admin_key:
                transaction.sign(admin_key)

            receipt = transaction.execute(client)
            if receipt.status != ResponseCode.SUCCESS:
                raise ValueError(f"Update failed: {ResponseCode.get_name(receipt.status)}")
            
            return True
        except Exception as e:
            raise ValueError(f"Topic update failed: {str(e)}")

    @staticmethod
    def delete_topic(topic_id, admin_key=None):
        """Delete a topic"""
        client = HederaService.get_client()
        
        try:
            transaction = TopicDeleteTransaction(
                topic_id=topic_id
            ).freeze_with(client).sign(client.operator_private_key)

            if admin_key:
                transaction.sign(admin_key)

            receipt = transaction.execute(client)
            if receipt.status != ResponseCode.SUCCESS:
                raise ValueError(f"Deletion failed: {ResponseCode.get_name(receipt.status)}")
            
            return True
        except Exception as e:
            raise ValueError(f"Topic deletion failed: {str(e)}")

    @staticmethod
    def get_topic_info(topic_id):
        """Get topic information"""
        try:
            return TopicInfoQuery(
                topic_id=topic_id
            ).execute(HederaService.get_client())
        except Exception as e:
            raise ValueError(f"Topic info query failed: {str(e)}")
        


try:
    token_id = HederaService.create_token(
        token_name="Quepter",
        token_symbol="QUEP",
        decimals=8,
        initial_supply=100_000_000
    )
    print(f"Created token: {token_id}")
except ValueError as e:
    print(f"Error: {e}")