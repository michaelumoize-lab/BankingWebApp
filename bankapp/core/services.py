from .models import BankAccount, Transaction
from django.db import transaction as db_transaction
from decimal import Decimal

def deposit(account: BankAccount, amount: Decimal, description: str = ""):
    if amount <= 0:
        raise ValueError("Deposit amount must be positive")

    with db_transaction.atomic():
        account.balance += amount
        account.save()
        Transaction.objects.create(
            account=account,
            amount=amount,
            transaction_type="DEPOSIT",
            description=description
        )
    return account.balance

def withdraw(account: BankAccount, amount: Decimal, description: str = ""):
    if amount <= 0:
        raise ValueError("Withdrawal amount must be positive")
    if account.balance < amount:
        raise ValueError("Insufficient balance")

    with db_transaction.atomic():
        account.balance -= amount
        account.save()
        Transaction.objects.create(
            account=account,
            amount=amount,
            transaction_type="WITHDRAW",
            description=description
        )
    return account.balance

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

        Transaction.objects.create(
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

    return sender.balance, receiver.balance
