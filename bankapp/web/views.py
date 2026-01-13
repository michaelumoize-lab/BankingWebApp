from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from core.models import BankAccount, User, ProfileUpdate, Notification, DebitCard, CardApplication, Loan, BankStatement, BillPayment, Review, Receipt
from core.services import deposit, withdraw, transfer, generate_receipt
from decimal import Decimal


def home(request):
    """Homepage for the bank"""
    if request.method == "POST":
        # Handle review submission
        name = request.POST.get("review_name")
        email = request.POST.get("review_email")
        rating = request.POST.get("review_rating")
        title = request.POST.get("review_title")
        message = request.POST.get("review_message")
        
        # Validation
        if name and email and rating and title and message:
            Review.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=name,
                email=email,
                rating=int(rating),
                title=title,
                message=message
            )
            return render(request, "web/home.html", {
                "success": "Thank you for your review! It will be displayed after admin approval.",
                "approved_reviews": Review.objects.filter(is_approved=True)
            })
        else:
            return render(request, "web/home.html", {
                "error": "Please fill in all fields",
                "approved_reviews": Review.objects.filter(is_approved=True)
            })
    
    approved_reviews = Review.objects.filter(is_approved=True).order_by('-created_at')[:10]
    return render(request, "web/home.html", {"approved_reviews": approved_reviews})

def get_or_create_account(user):
    """Get or create bank account for user"""
    account, created = BankAccount.objects.get_or_create(user=user)
    return account

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user:
            if not user.is_approved:
                return render(request, "web/login.html", {"error": "Your account is pending admin approval. Please check back soon."})
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "web/login.html", {"error": "Invalid credentials"})
    return render(request, "web/login.html")

def logout_view(request):
    logout(request)
    return redirect("login")

def signup_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone = request.POST.get("phone")
        
        # Validation
        errors = []
        
        if not email:
            errors.append("Email is required")
        elif User.objects.filter(email=email).exists():
            errors.append("Email already registered")
        
        if not password:
            errors.append("Password is required")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters")
        
        if password != password_confirm:
            errors.append("Passwords do not match")
        
        if errors:
            return render(request, "web/signup.html", {"errors": errors})
        
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            is_approved=False  # Pending admin approval
        )
        
        # Create debit card for user
        card_holder_name = f"{first_name} {last_name}".strip()
        DebitCard.objects.create(
            user=user,
            card_holder_name=card_holder_name,
            status="PENDING"
        )
        
        return render(request, "web/signup_success.html", {"email": email})
    
    return render(request, "web/signup.html")

@login_required
def dashboard(request):
    account = get_or_create_account(request.user)
    recent_transactions = account.transactions.all().order_by('-timestamp')[:10]
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False)
    debit_card = DebitCard.objects.filter(user=request.user).first()
    
    # Auto-mark notifications as read when dashboard is viewed
    # (but still show them for this page load)
    if unread_notifications.exists():
        unread_notifications.update(is_read=True)
    
    return render(request, "web/dashboard.html", {
        "account": account, 
        "recent_transactions": recent_transactions,
        "unread_notifications": unread_notifications,
        "debit_card": debit_card,
    })

@login_required
@login_required
def deposit_view(request):
    account = get_or_create_account(request.user)
    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get("amount"))
            txn = deposit(account, amount, "Web deposit")
            
            # Generate receipt
            receipt = generate_receipt(
                user=request.user,
                transaction_type='deposit',
                amount=amount,
                description='Web deposit',
                from_account='',
                to_account=account.account_number,
                recipient_name=f"{request.user.first_name} {request.user.last_name}"
            )
            
            # Link transaction to receipt
            txn.receipt = receipt
            txn.save()
            
            return redirect('receipt_view', receipt_id=receipt.id)
        except (ValueError, Exception) as e:
            return render(request, "web/deposit.html", {"account": account, "error": str(e)})
    return render(request, "web/deposit.html", {"account": account})

@login_required
def withdraw_view(request):
    account = get_or_create_account(request.user)
    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get("amount"))
            txn = withdraw(account, amount, "Web withdrawal")
            
            # Generate receipt
            receipt = generate_receipt(
                user=request.user,
                transaction_type='withdraw',
                amount=amount,
                description='Web withdrawal',
                from_account=account.account_number,
                to_account='',
                recipient_name=f"{request.user.first_name} {request.user.last_name}"
            )
            
            # Link transaction to receipt
            txn.receipt = receipt
            txn.save()
            
            return redirect('receipt_view', receipt_id=receipt.id)
        except (ValueError, Exception) as e:
            return render(request, "web/withdraw.html", {"account": account, "error": str(e)})
    return render(request, "web/withdraw.html", {"account": account})

@login_required
def transfer_view(request):
    account = get_or_create_account(request.user)
    if request.method == "POST":
        try:
            recipient_account_number = request.POST.get("recipient_account_number", "").strip()
            amount = Decimal(request.POST.get("amount"))
            
            # Validate account number
            if not recipient_account_number:
                raise ValueError("Please enter a recipient account number")
            
            # Find recipient account
            receiver_account = BankAccount.objects.get(account_number=recipient_account_number)
            
            # Prevent self-transfer
            if receiver_account.user_id == request.user.id:
                raise ValueError("You cannot transfer to your own account")
            
            # Check if recipient account is active
            if not receiver_account.is_active:
                raise ValueError("Recipient account is not active")
            
            txn = transfer(account, receiver_account, amount, "Web transfer")
            
            # Generate receipt
            receipt = generate_receipt(
                user=request.user,
                transaction_type='transfer',
                amount=amount,
                description='Web transfer',
                from_account=account.account_number,
                to_account=receiver_account.account_number,
                recipient_name=f"{receiver_account.user.first_name} {receiver_account.user.last_name}"
            )
            
            # Link transaction to receipt
            txn.receipt = receipt
            txn.save()
            
            return redirect('receipt_view', receipt_id=receipt.id)
        except BankAccount.DoesNotExist:
            return render(request, "web/transfer.html", {"account": account, "error": "Account number not found"})
        except ValueError as e:
            return render(request, "web/transfer.html", {"account": account, "error": str(e)})
        except Exception as e:
            return render(request, "web/transfer.html", {"account": account, "error": str(e)})
    return render(request, "web/transfer.html", {"account": account})

@login_required
def profile_view(request):
    """Display user profile"""
    pending_update = ProfileUpdate.objects.filter(user=request.user, status='PENDING').first()
    context = {
        'pending_update': pending_update,
    }
    return render(request, "web/profile.html", context)

@login_required
def edit_profile_view(request):
    """Edit user profile - creates pending update"""
    pending_update = ProfileUpdate.objects.filter(user=request.user, status='PENDING').first()
    
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        
        # Create or update pending profile update
        if pending_update:
            pending_update.first_name = first_name
            pending_update.last_name = last_name
            pending_update.phone = phone
            pending_update.requested_at = timezone.now()
            pending_update.save()
        else:
            ProfileUpdate.objects.create(
                user=request.user,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
            )
        
        return render(request, "web/edit_profile.html", {
            "success": True,
            "pending_update": pending_update,
        })
    
    context = {
        'pending_update': pending_update,
    }
    return render(request, "web/edit_profile.html", context)


@login_required
def mark_notification_as_read(request, notification_id):
    """API endpoint to mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({"status": "success"})
    except Notification.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Notification not found"}, status=404)


@login_required
def pay_card_fee(request):
    """Pay debit card issuance fee"""
    account = get_or_create_account(request.user)
    debit_card = DebitCard.objects.filter(user=request.user).first()
    
    if not debit_card:
        return render(request, "web/pay_card_fee.html", {"error": "No debit card found"})
    
    if debit_card.card_fee_paid:
        return render(request, "web/pay_card_fee.html", {"error": "Card fee already paid", "debit_card": debit_card})
    
    if request.method == "POST":
        try:
            # Deduct $10 fee from account
            fee_amount = Decimal("10.00")
            
            if account.balance < fee_amount:
                return render(request, "web/pay_card_fee.html", {
                    "account": account,
                    "debit_card": debit_card,
                    "error": f"Insufficient balance. You need ${fee_amount} to issue your debit card."
                })
            
            # Process payment
            from core.services import withdraw
            withdraw(account, fee_amount, "Debit Card Issuance Fee")
            
            # Issue card
            debit_card.issue_card()
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                title="Debit Card Activated",
                message=f"Your debit card ending in {debit_card.card_number[-4:]} has been activated.",
                notification_type="INFO"
            )
            
            return render(request, "web/pay_card_fee.html", {
                "success": True,
                "debit_card": debit_card,
                "account": account
            })
        except Exception as e:
            return render(request, "web/pay_card_fee.html", {
                "account": account,
                "debit_card": debit_card,
                "error": str(e)
            })
    
    return render(request, "web/pay_card_fee.html", {
        "account": account,
        "debit_card": debit_card,
    })


@login_required
def view_debit_card(request):
    """View debit card details"""
    debit_card = DebitCard.objects.filter(user=request.user).first()
    
    if not debit_card:
        return render(request, "web/view_card.html", {"error": "No debit card found"})
    
    if not debit_card.card_fee_paid:
        return render(request, "web/view_card.html", {
            "error": "Card fee not paid. Please pay the $10 fee to activate your card.",
            "debit_card": debit_card,
        })
    
    return render(request, "web/view_card.html", {"debit_card": debit_card})


@login_required
def notifications_list(request):
    """View all notifications history"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read when viewing notifications page
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, "web/notifications.html", {
        "notifications": notifications,
        "unread_count": unread_count,
    })


@login_required
def apply_for_card(request):
    """User applies for a new debit card"""
    # Check if user already has a pending or approved application
    existing_app = CardApplication.objects.filter(
        user=request.user, 
        status__in=['PENDING', 'APPROVED']
    ).first()
    
    if existing_app:
        return render(request, "web/apply_card.html", {
            "existing_app": existing_app,
            "message": "You already have a pending card application."
        })
    
    if request.method == "POST":
        purpose = request.POST.get("purpose", "").strip()
        
        if not purpose:
            return render(request, "web/apply_card.html", {
                "error": "Please tell us why you need a debit card."
            })
        
        # Create card application
        card_app = CardApplication.objects.create(
            user=request.user,
            card_type="DEBIT",
            purpose=purpose
        )
        
        return render(request, "web/apply_card.html", {
            "success": True,
            "card_app": card_app,
        })
    
    return render(request, "web/apply_card.html")


# ==================== LOAN VIEWS ====================

@login_required
def apply_for_loan(request):
    """User applies for a loan"""
    existing_app = Loan.objects.filter(
        user=request.user, 
        status__in=['PENDING', 'APPROVED']
    ).first()
    
    if existing_app:
        return render(request, "web/apply_loan.html", {
            "existing_loan": existing_app,
            "message": "You already have a pending or approved loan application."
        })
    
    if request.method == "POST":
        loan_type = request.POST.get("loan_type", "").strip()
        loan_amount = request.POST.get("loan_amount", "").strip()
        interest_rate = request.POST.get("interest_rate", "").strip()
        loan_term_months = request.POST.get("loan_term_months", "").strip()
        purpose = request.POST.get("purpose", "").strip()
        employment_status = request.POST.get("employment_status", "").strip()
        annual_income = request.POST.get("annual_income", "").strip()
        collateral = request.POST.get("collateral", "").strip()
        
        errors = []
        
        if not loan_type or loan_type not in [choice[0] for choice in Loan.LOAN_TYPES]:
            errors.append("Invalid loan type selected")
        
        try:
            loan_amount = Decimal(loan_amount)
            if loan_amount <= 0:
                errors.append("Loan amount must be greater than 0")
        except:
            errors.append("Invalid loan amount")
        
        try:
            interest_rate = Decimal(interest_rate)
            if interest_rate < 0:
                errors.append("Interest rate cannot be negative")
        except:
            errors.append("Invalid interest rate")
        
        try:
            loan_term_months = int(loan_term_months)
            if loan_term_months <= 0:
                errors.append("Loan term must be greater than 0")
        except:
            errors.append("Invalid loan term")
        
        if not purpose:
            errors.append("Please provide purpose for the loan")
        
        if errors:
            return render(request, "web/apply_loan.html", {
                "errors": errors,
                "loan_types": Loan.LOAN_TYPES,
            })
        
        # Create loan application
        loan = Loan.objects.create(
            user=request.user,
            loan_type=loan_type,
            loan_amount=loan_amount,
            interest_rate=interest_rate,
            loan_term_months=loan_term_months,
            purpose=purpose,
            employment_status=employment_status,
            annual_income=Decimal(annual_income) if annual_income else None,
            collateral_details=collateral
        )
        
        loan.calculate_monthly_payment()
        loan.save()
        
        return render(request, "web/apply_loan.html", {
            "success": True,
            "loan": loan,
        })
    
    return render(request, "web/apply_loan.html", {
        "loan_types": Loan.LOAN_TYPES,
    })


@login_required
def loan_applications_list(request):
    """List all loan applications for the user"""
    loans = Loan.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'loans': loans,
    }
    return render(request, 'web/loan_applications.html', context)


@login_required
def loan_detail(request, loan_id):
    """View loan details"""
    try:
        loan = Loan.objects.get(id=loan_id, user=request.user)
    except Loan.DoesNotExist:
        return render(request, "web/error.html", {"error": "Loan not found"})
    
    context = {
        'loan': loan,
    }
    return render(request, 'web/loan_detail.html', context)


# ==================== BANK STATEMENT VIEWS ====================

@login_required
def request_bank_statement(request):
    """Request a bank statement for a specific period"""
    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        format_type = request.POST.get("format_type", "PDF")
        
        errors = []
        
        try:
            from datetime import datetime
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            if start > end:
                errors.append("Start date cannot be after end date")
            if end > timezone.now().date():
                errors.append("End date cannot be in the future")
        except:
            errors.append("Invalid date format")
        
        if format_type not in ["PDF", "CSV"]:
            errors.append("Invalid format type")
        
        if errors:
            return render(request, "web/request_bank_statement.html", {"errors": errors})
        
        # Get transactions in the date range
        account = get_or_create_account(request.user)
        transactions = account.transactions.filter(
            timestamp__date__gte=start,
            timestamp__date__lte=end
        ).order_by('timestamp')
        
        # Calculate opening and closing balance
        opening_balance = account.balance
        for txn in transactions.reverse():
            if txn.transaction_type == "DEPOSIT":
                opening_balance -= txn.amount
            elif txn.transaction_type == "WITHDRAW":
                opening_balance += txn.amount
        
        closing_balance = account.balance
        
        # Create bank statement request
        statement = BankStatement.objects.create(
            user=request.user,
            start_date=start,
            end_date=end,
            format_type=format_type,
            status="GENERATED",
            transaction_count=transactions.count(),
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            generated_at=timezone.now()
        )
        
        Notification.objects.create(
            user=request.user,
            title="Bank Statement Generated",
            message=f"Your bank statement for {start} to {end} has been generated and is ready for download.",
            notification_type="INFO",
            related_object_id=str(statement.id)
        )
        
        return render(request, "web/request_bank_statement.html", {
            "success": True,
            "statement": statement,
        })
    
    return render(request, "web/request_bank_statement.html")


@login_required
def bank_statements_list(request):
    """List all bank statements for the user"""
    statements = BankStatement.objects.filter(user=request.user).order_by('-requested_at')
    
    context = {
        'statements': statements,
    }
    return render(request, 'web/bank_statements.html', context)


# ==================== BILL PAYMENT VIEWS ====================

@login_required
def pay_bill(request):
    """Pay a bill"""
    if request.method == "POST":
        bill_type = request.POST.get("bill_type", "").strip()
        provider_name = request.POST.get("provider_name", "").strip()
        account_number = request.POST.get("account_number", "").strip()
        amount = request.POST.get("amount", "").strip()
        due_date = request.POST.get("due_date", "").strip()
        pin = request.POST.get("pin", "").strip()
        
        errors = []
        
        if not bill_type or bill_type not in [choice[0] for choice in BillPayment.BILL_TYPES]:
            errors.append("Invalid bill type")
        
        if not provider_name:
            errors.append("Please enter provider name")
        
        if not account_number:
            errors.append("Please enter your account number with the provider")
        
        try:
            amount = Decimal(amount)
            if amount <= 0:
                errors.append("Amount must be greater than 0")
        except:
            errors.append("Invalid amount")
        
        # Verify PIN
        if pin != request.user.pin:
            errors.append("Invalid PIN")
        
        # Check balance
        account = get_or_create_account(request.user)
        if account.balance < amount:
            errors.append("Insufficient balance")
        
        if errors:
            return render(request, "web/pay_bill.html", {
                "errors": errors,
                "bill_types": BillPayment.BILL_TYPES,
            })
        
        # Process bill payment
        import random
        import string
        reference_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        bill_payment = BillPayment.objects.create(
            user=request.user,
            bill_type=bill_type,
            provider_name=provider_name,
            account_number=account_number,
            amount=amount,
            due_date=due_date if due_date else timezone.now().date(),
            reference_number=reference_number,
            status="COMPLETED",
            paid_at=timezone.now()
        )
        
        # Deduct from account
        account.balance -= amount
        account.save()
        
        # Create transaction record
        from core.models import Transaction
        Transaction.objects.create(
            account=account,
            amount=amount,
            transaction_type="WITHDRAW",
            description=f"Bill Payment - {provider_name} ({bill_type})",
        )
        
        Notification.objects.create(
            user=request.user,
            title="Bill Payment Successful",
            message=f"Your bill payment of ${amount} to {provider_name} has been completed. Reference: {reference_number}",
            notification_type="INFO",
            related_object_id=str(bill_payment.id)
        )
        
        return render(request, "web/pay_bill.html", {
            "success": True,
            "bill_payment": bill_payment,
        })
    
    return render(request, "web/pay_bill.html", {
        "bill_types": BillPayment.BILL_TYPES,
    })


@login_required
def bill_payments_list(request):
    """List all bill payments for the user"""
    payments = BillPayment.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'payments': payments,
    }
    return render(request, 'web/bill_payments.html', context)


@login_required
def receipt_view(request, receipt_id):
    """Display transaction receipt"""
    receipt = get_object_or_404(Receipt, id=receipt_id, user=request.user)
    return render(request, 'web/receipt.html', {'receipt': receipt})


@login_required
def receipts_list(request):
    """List all receipts for user"""
    receipts = Receipt.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'web/receipts_list.html', {'receipts': receipts})
