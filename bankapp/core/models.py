from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
import uuid
import random


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


def generate_pin():
    """Generate a random 4-digit PIN"""
    return str(random.randint(1000, 9999))


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    pin = models.CharField(max_length=4, default=generate_pin, help_text="4-digit PIN for transaction authentication")
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False, help_text="Admin approval required for customer accounts")
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"

    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


def generate_account_number():
    return str(random.randint(1000000000, 9999999999))


class BankAccount(models.Model):
    ACCOUNT_TYPES = (
        ("SAVINGS", "Savings"),
        ("CURRENT", "Current"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    account_number = models.CharField(
        max_length=10,
        unique=True,
        default=generate_account_number
    )
    account_type = models.CharField(
        max_length=10,
        choices=ACCOUNT_TYPES,
        default="SAVINGS"
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_number} - {self.user.email}"
    
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ("DEPOSIT", "Deposit"),
        ("WITHDRAW", "Withdraw"),
        ("TRANSFER", "Transfer"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"


class ProfileUpdate(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="profile_updates"
    )
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profile_reviews"
    )
    rejection_reason = models.TextField(blank=True)

    class Meta:
        verbose_name = "Profile Update"
        verbose_name_plural = "Profile Updates"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.user.email} - {self.status}"
    
    def approve(self, admin_user):
        """Approve the profile update and apply changes to user"""
        self.user.first_name = self.first_name
        self.user.last_name = self.last_name
        self.user.phone = self.phone
        self.user.save()
        
        self.status = "APPROVED"
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()
        
        # Create notification
        Notification.objects.create(
            user=self.user,
            title="Profile Update Approved",
            message="Your profile changes have been approved and applied to your account.",
            notification_type="APPROVAL",
            related_object_id=str(self.id)
        )
    
    def reject(self, admin_user, reason=""):
        """Reject the profile update"""
        self.status = "REJECTED"
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()
        
        # Create notification
        Notification.objects.create(
            user=self.user,
            title="Profile Update Rejected",
            message=f"Your profile changes were not approved. Reason: {reason}" if reason else "Your profile changes were not approved.",
            notification_type="REJECTION",
            related_object_id=str(self.id)
        )


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ("APPROVAL", "Approval"),
        ("REJECTION", "Rejection"),
        ("SECURITY", "Security Alert"),
        ("INFO", "Information"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default="INFO")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()


def generate_card_number():
    """Generate a 16-digit card number"""
    return ''.join([str(random.randint(0, 9)) for _ in range(16)])


def generate_cvv():
    """Generate a 3-digit CVV"""
    return ''.join([str(random.randint(0, 9)) for _ in range(3)])


def generate_expiry_date():
    """Generate expiry date (4 years from now)"""
    expiry = timezone.now() + timezone.timedelta(days=365*4)
    return expiry.strftime('%m/%y')


class DebitCard(models.Model):
    CARD_STATUS_CHOICES = (
        ("PENDING", "Pending (Fee Not Paid)"),
        ("ACTIVE", "Active (Issued)"),
        ("BLOCKED", "Blocked"),
        ("EXPIRED", "Expired"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="debit_card"
    )
    card_number = models.CharField(max_length=16, unique=True, default=generate_card_number)
    card_holder_name = models.CharField(max_length=100)
    expiry_date = models.CharField(max_length=5, default=generate_expiry_date)  # MM/YY format
    cvv = models.CharField(max_length=3, default=generate_cvv)
    status = models.CharField(max_length=20, choices=CARD_STATUS_CHOICES, default="PENDING")
    card_fee_paid = models.BooleanField(default=False)
    card_fee_amount = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    issued_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.card_number[-4:]} ({self.status})"

    def issue_card(self):
        """Mark card as issued after fee payment"""
        self.status = "ACTIVE"
        self.card_fee_paid = True
        self.issued_at = timezone.now()
        self.save()

class CardApplication(models.Model):
    APPLICATION_STATUS_CHOICES = (
        ("PENDING", "Pending Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="card_applications")
    card_type = models.CharField(max_length=20, default="DEBIT")  # DEBIT, CREDIT, etc.
    purpose = models.TextField(help_text="Why do you need this card?")
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default="PENDING")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_card_applications")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection if applicable")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.card_type} ({self.status})"

    class Meta:
        verbose_name = "Card Application"
        verbose_name_plural = "Card Applications"

    def approve(self, admin_user):
        """Approve card application and create debit card"""
        self.status = "APPROVED"
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()

        # Create debit card if approved
        card_holder_name = f"{self.user.first_name} {self.user.last_name}".strip()
        DebitCard.objects.create(
            user=self.user,
            card_holder_name=card_holder_name,
            status="PENDING"
        )

        # Create notification
        Notification.objects.create(
            user=self.user,
            title="Card Application Approved",
            message="Your card application has been approved. You can now pay the $10 fee to activate your card.",
            notification_type="APPROVAL"
        )

    def reject(self, admin_user, reason=""):
        """Reject card application"""
        self.status = "REJECTED"
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()

        # Create notification
        Notification.objects.create(
            user=self.user,
            title="Card Application Rejected",
            message=f"Your card application has been rejected. Reason: {reason}",
            notification_type="REJECTION"
        )


class Loan(models.Model):
    LOAN_TYPES = (
        ("PERSONAL", "Personal Loan"),
        ("HOME", "Home Loan"),
        ("AUTO", "Auto Loan"),
        ("EDUCATION", "Education Loan"),
        ("BUSINESS", "Business Loan"),
    )
    
    STATUS_CHOICES = (
        ("PENDING", "Pending Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loans")
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual interest rate (%)")
    loan_term_months = models.IntegerField(help_text="Loan duration in months")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    purpose = models.TextField(help_text="Purpose of the loan")
    employment_status = models.CharField(max_length=50, blank=True, help_text="Employment status of applicant")
    annual_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    collateral_details = models.TextField(blank=True, help_text="Details of collateral if any")
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Calculated monthly payment")
    total_repayment = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total amount to be repaid")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_loans")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    disbursed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.get_loan_type_display()} ({self.status})"

    class Meta:
        verbose_name = "Loan"
        verbose_name_plural = "Loans"
        ordering = ["-created_at"]

    def calculate_monthly_payment(self):
        """Calculate monthly payment using EMI formula"""
        principal = float(self.loan_amount)
        monthly_rate = float(self.interest_rate) / 12 / 100
        num_payments = self.loan_term_months
        
        if monthly_rate == 0:
            monthly_payment = principal / num_payments
        else:
            monthly_payment = (principal * monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        
        self.monthly_payment = round(monthly_payment, 2)
        self.total_repayment = round(monthly_payment * num_payments, 2)
        return self.monthly_payment

    def approve(self, admin_user):
        """Approve loan application"""
        self.status = "APPROVED"
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.calculate_monthly_payment()
        self.save()

        # Create notification
        Notification.objects.create(
            user=self.user,
            title="Loan Application Approved",
            message=f"Your {self.get_loan_type_display()} application for ${self.loan_amount} has been approved. Monthly payment: ${self.monthly_payment}",
            notification_type="APPROVAL",
            related_object_id=str(self.id)
        )

    def reject(self, admin_user, reason=""):
        """Reject loan application"""
        self.status = "REJECTED"
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()

        # Create notification
        Notification.objects.create(
            user=self.user,
            title="Loan Application Rejected",
            message=f"Your {self.get_loan_type_display()} application has been rejected. Reason: {reason}",
            notification_type="REJECTION",
            related_object_id=str(self.id)
        )

    def disburse(self):
        """Disburse approved loan to user account"""
        if self.status != "APPROVED":
            raise ValueError("Only approved loans can be disbursed")
        
        try:
            bank_account = self.user.bankaccount
            bank_account.balance += self.loan_amount
            bank_account.save()
            
            self.status = "ACTIVE"
            self.disbursed_amount = self.loan_amount
            self.disbursed_at = timezone.now()
            self.save()

            # Create notification
            Notification.objects.create(
                user=self.user,
                title="Loan Disbursed",
                message=f"Your {self.get_loan_type_display()} of ${self.loan_amount} has been disbursed to your account.",
                notification_type="INFO",
                related_object_id=str(self.id)
            )
        except:
            raise ValueError("Bank account not found for user")


class BankStatement(models.Model):
    REQUEST_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("GENERATED", "Generated"),
        ("READY", "Ready for Download"),
        ("EXPIRED", "Expired"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="statement_requests")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default="PENDING")
    format_type = models.CharField(max_length=10, choices=[("PDF", "PDF"), ("CSV", "CSV")], default="PDF")
    statement_file = models.FileField(upload_to="statements/", null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    transaction_count = models.IntegerField(default=0)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.email} - {self.start_date} to {self.end_date}"

    class Meta:
        verbose_name = "Bank Statement"
        verbose_name_plural = "Bank Statements"
        ordering = ["-requested_at"]


class BillPayment(models.Model):
    BILL_TYPES = (
        ("ELECTRICITY", "Electricity"),
        ("WATER", "Water"),
        ("GAS", "Gas"),
        ("INTERNET", "Internet"),
        ("MOBILE", "Mobile Phone"),
        ("INSURANCE", "Insurance"),
        ("LOAN", "Loan EMI"),
        ("CREDIT_CARD", "Credit Card Bill"),
        ("OTHER", "Other"),
    )

    PAYMENT_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bill_payments")
    bill_type = models.CharField(max_length=20, choices=BILL_TYPES)
    provider_name = models.CharField(max_length=100, help_text="Name of the bill provider")
    account_number = models.CharField(max_length=100, help_text="Your account number with the provider")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="PENDING")
    reference_number = models.CharField(max_length=100, unique=True, blank=True)
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.get_bill_type_display()} ({self.status})"

    class Meta:
        verbose_name = "Bill Payment"
        verbose_name_plural = "Bill Payments"
        ordering = ["-created_at"]


class Review(models.Model):
    RATING_CHOICES = (
        (1, "⭐ Poor"),
        (2, "⭐⭐ Fair"),
        (3, "⭐⭐⭐ Good"),
        (4, "⭐⭐⭐⭐ Very Good"),
        (5, "⭐⭐⭐⭐⭐ Excellent"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews", null=True, blank=True)
    name = models.CharField(max_length=100, help_text="Reviewer name (if not logged in)")
    email = models.EmailField(help_text="Reviewer email (if not logged in)")
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200, help_text="Review title")
    message = models.TextField(help_text="Your review message")
    is_approved = models.BooleanField(default=False, help_text="Admin approval before display")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.get_rating_display()}"

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-created_at"]