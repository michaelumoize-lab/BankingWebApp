from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Import your custom User model
from core.models import User, BankAccount

@receiver(post_save, sender=User)
def create_account(sender, instance, created, **kwargs):
    if created:
        # Auto-create a bank account for new users
        BankAccount.objects.create(
            user=instance,
            account_number=f"ACC{str(instance.id)[:8]}",
            balance=0
        )
