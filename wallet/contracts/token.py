from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

def create_qpt_token(client):
    admin_key = PrivateKey.generate()
    supply_key = PrivateKey.generate()
    freeze_key = PrivateKey.generate()

    transaction = TokenCreateTransaction(
        token_name="Quepter",
        token_symbol="QPT",
        decimals=2,
        initial_supply=100_000_000,
        treasury_account_id=client.get_operator_account_id(),
        admin_key=admin_key.get_public_key(),
        supply_key=supply_key.get_public_key(),
        freeze_key=freeze_key.get_public_key()
    ).freeze_with(client).sign(client.operator_private_key)

    transaction.sign(admin_key)
    receipt = transaction.execute(client).get_receipt(client)

    if receipt.tokenId:
        print(f"✅ QPT Token Created Successfully! Token ID: {receipt.tokenId}")
        return receipt.tokenId, admin_key, supply_key, freeze_key
    else:
        raise Exception("❌ Failed to create QPT token.")

def transfer_qpt(client, sender_id, sender_key, receiver_id, token_id, amount):
    transaction = (
        TransferTransaction()
        .add_token_transfer(token_id, sender_id, -amount)
        .add_token_transfer(token_id, receiver_id, amount)
        .freeze_with(client)
        .sign(sender_key)
    )

    receipt = transaction.execute(client).get_receipt(client)

    if receipt.status.to_string() == "SUCCESS":
        print(f"✅ {amount} QPT transferred from {sender_id} to {receiver_id}")
