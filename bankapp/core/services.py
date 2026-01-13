from .models import BankAccount, Transaction, Receipt
from django.db import transaction as db_transaction
from decimal import Decimal
import uuid

def generate_receipt(user, transaction_type, amount, description, from_account="", to_account="", recipient_name="", status="completed"):
    """Generate a receipt for any transaction"""
    reference_number = f"{transaction_type.upper()}-{str(uuid.uuid4())[:8].upper()}"
    
    receipt = Receipt.objects.create(
        user=user,
        transaction_type=transaction_type,
        amount=amount,
        reference_number=reference_number,
        description=description,
        from_account=from_account,
        to_account=to_account,
        recipient_name=recipient_name,
        status=status
    )
    return receipt

def deposit(account: BankAccount, amount: Decimal, description: str = ""):
    if amount <= 0:
        raise ValueError("Deposit amount must be positive")

    with db_transaction.atomic():
        account.balance += amount
        account.save()
        txn = Transaction.objects.create(
            account=account,
            amount=amount,
            transaction_type="DEPOSIT",
            description=description
        )
    return txn

def withdraw(account: BankAccount, amount: Decimal, description: str = ""):
    if amount <= 0:
        raise ValueError("Withdrawal amount must be positive")
    if account.balance < amount:
        raise ValueError("Insufficient balance")

    with db_transaction.atomic():
        account.balance -= amount
        account.save()
        txn = Transaction.objects.create(
            account=account,
            amount=amount,
            transaction_type="WITHDRAW",
            description=description
        )
    return txn

def transfer(sender: BankAccount, receiver: BankAccount, amount: Decimal, description: str = ""):
    if sender == receiver:
        raise ValueError("Cannot transfer to the same account")
    if amount <= 0:
        raise ValueError("Transfer amount must be positive")
    if sender.balance < amount:
        raise ValueError("Insufficient balance")

    with db_transaction.atomic():
        sender.balance -= amount
        receiver.balance += amount
        sender.save()
        receiver.save()

        txn = Transaction.objects.create(
            account=sender,
            amount=amount,
            transaction_type="TRANSFER",
            description=f"Sent to {receiver.account_number}. {description}"
        )

        Transaction.objects.create(
            account=receiver,
            amount=amount,
            transaction_type="TRANSFER",
            description=f"Received from {sender.account_number}. {description}"
        )

    return txn
