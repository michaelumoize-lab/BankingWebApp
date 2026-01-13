from django.contrib import admin
from django.utils import timezone
from .models import User, BankAccount, Transaction, ProfileUpdate, Notification, DebitCard, CardApplication, Loan, BankStatement, BillPayment, Review, Receipt

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_approved', 'is_active', 'date_joined')
    list_filter = ('is_approved', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = (
        ('Account Info', {'fields': ('email', 'first_name', 'last_name', 'phone')}),
        ('Status', {'fields': ('is_approved', 'is_active')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('date_joined', 'last_login')
    
    actions = ['approve_users', 'disapprove_users']
    
    def approve_users(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, "Selected users have been approved.")
    approve_users.short_description = "Approve selected users"
    
    def disapprove_users(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, "Selected users have been disapproved.")
    disapprove_users.short_description = "Disapprove selected users"

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user', 'account_type', 'balance', 'is_active')
    list_filter = ('account_type', 'is_active')
    search_fields = ('account_number', 'user__email')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'account', 'amount', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('account__account_number', 'description')

@admin.register(ProfileUpdate)
class ProfileUpdateAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'requested_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'requested_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('user', 'requested_at', 'reviewed_at', 'reviewed_by')
    fieldsets = (
        ('User Info', {'fields': ('user', 'requested_at')}),
        ('Requested Changes', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Review', {'fields': ('status', 'rejection_reason', 'reviewed_by', 'reviewed_at')}),
    )
    
    actions = ['approve_updates', 'reject_updates']
    
    def approve_updates(self, request, queryset):
        for update in queryset.filter(status='PENDING'):
            update.approve(request.user)
        self.message_user(request, "Selected profile updates have been approved.")
    approve_updates.short_description = "Approve selected profile updates"
    
    def reject_updates(self, request, queryset):
        queryset.filter(status='PENDING').update(status='REJECTED', reviewed_by=request.user)
        self.message_user(request, "Selected profile updates have been rejected.")
    reject_updates.short_description = "Reject selected profile updates"

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__email', 'title', 'message')
    readonly_fields = ('user', 'title', 'message', 'notification_type', 'created_at')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, "Selected notifications marked as read.")
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, "Selected notifications marked as unread.")
    mark_as_unread.short_description = "Mark selected as unread"

@admin.register(DebitCard)
class DebitCardAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_number', 'card_holder_name', 'status', 'card_fee_paid', 'issued_at')
    list_filter = ('status', 'card_fee_paid', 'created_at')
    search_fields = ('user__email', 'card_number', 'card_holder_name')
    readonly_fields = ('card_number', 'cvv', 'expiry_date', 'created_at', 'issued_at', 'id')
    fieldsets = (
        ('Card Information', {'fields': ('id', 'user', 'card_number', 'card_holder_name')}),
        ('Card Details', {'fields': ('cvv', 'expiry_date')}),
        ('Status & Payment', {'fields': ('status', 'card_fee_paid', 'card_fee_amount')}),
        ('Timestamps', {'fields': ('created_at', 'issued_at')}),
    )
    
    actions = ['mark_card_active', 'block_card']
    
    def mark_card_active(self, request, queryset):
        queryset.update(status='ACTIVE', card_fee_paid=True)
        self.message_user(request, "Selected cards marked as active.")
    mark_card_active.short_description = "Mark selected cards as active"
    
    def block_card(self, request, queryset):
        queryset.update(status='BLOCKED')
        self.message_user(request, "Selected cards blocked.")
    block_card.short_description = "Block selected cards"


@admin.register(CardApplication)
class CardApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_type', 'status', 'created_at', 'reviewed_at')
    list_filter = ('status', 'card_type', 'created_at')
    search_fields = ('user__email', 'purpose')
    readonly_fields = ('id', 'created_at', 'updated_at', 'reviewed_at')
    fieldsets = (
        ('Application Info', {'fields': ('id', 'user', 'card_type', 'purpose')}),
        ('Status & Review', {'fields': ('status', 'reviewed_by', 'reviewed_at', 'rejection_reason')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    actions = ['approve_applications', 'reject_applications']

    def approve_applications(self, request, queryset):
        for app in queryset.filter(status='PENDING'):
            app.approve(request.user)
        self.message_user(request, f"Approved {queryset.count()} card application(s).")

    approve_applications.short_description = "Approve selected applications"

    def reject_applications(self, request, queryset):
        for app in queryset.filter(status='PENDING'):
            app.reject(request.user, "Rejected by admin")
        self.message_user(request, f"Rejected {queryset.count()} card application(s).")

    reject_applications.short_description = "Reject selected applications"


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('user', 'loan_type', 'loan_amount', 'status', 'created_at', 'reviewed_at')
    list_filter = ('status', 'loan_type', 'created_at')
    search_fields = ('user__email', 'purpose')
    readonly_fields = ('id', 'created_at', 'updated_at', 'reviewed_at', 'monthly_payment', 'total_repayment', 'disbursed_at')
    fieldsets = (
        ('Application Info', {'fields': ('id', 'user', 'loan_type', 'loan_amount', 'interest_rate', 'loan_term_months')}),
        ('Applicant Details', {'fields': ('employment_status', 'annual_income', 'purpose', 'collateral_details')}),
        ('Calculation', {'fields': ('monthly_payment', 'total_repayment')}),
        ('Status & Review', {'fields': ('status', 'reviewed_by', 'reviewed_at', 'rejection_reason')}),
        ('Disbursement', {'fields': ('disbursed_amount', 'disbursed_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    actions = ['approve_loans', 'reject_loans', 'disburse_loans']

    def approve_loans(self, request, queryset):
        for loan in queryset.filter(status='PENDING'):
            loan.approve(request.user)
        self.message_user(request, f"Approved {queryset.count()} loan application(s).")

    approve_loans.short_description = "Approve selected loan applications"

    def reject_loans(self, request, queryset):
        for loan in queryset.filter(status='PENDING'):
            loan.reject(request.user, "Rejected by admin")
        self.message_user(request, f"Rejected {queryset.count()} loan application(s).")

    reject_loans.short_description = "Reject selected loan applications"

    def disburse_loans(self, request, queryset):
        count = 0
        for loan in queryset.filter(status='APPROVED'):
            try:
                loan.disburse()
                count += 1
            except Exception as e:
                self.message_user(request, f"Error disbursing loan for {loan.user.email}: {str(e)}", level='error')
        self.message_user(request, f"Disbursed {count} loan(s).")

    disburse_loans.short_description = "Disburse approved loans"


@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_date', 'end_date', 'status', 'transaction_count', 'requested_at')
    list_filter = ('status', 'format_type', 'requested_at')
    search_fields = ('user__email',)
    readonly_fields = ('id', 'requested_at', 'generated_at', 'transaction_count', 'opening_balance', 'closing_balance')
    fieldsets = (
        ('Request Info', {'fields': ('id', 'user', 'start_date', 'end_date', 'format_type')}),
        ('Status & Timestamps', {'fields': ('status', 'requested_at', 'generated_at')}),
        ('Statement Details', {'fields': ('transaction_count', 'opening_balance', 'closing_balance')}),
        ('File', {'fields': ('statement_file',)}),
    )

    actions = ['mark_as_ready']

    def mark_as_ready(self, request, queryset):
        queryset.filter(status='GENERATED').update(status='READY')
        self.message_user(request, f"Marked {queryset.count()} statement(s) as ready.")

    mark_as_ready.short_description = "Mark selected statements as ready"


@admin.register(BillPayment)
class BillPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'bill_type', 'provider_name', 'amount', 'status', 'due_date', 'created_at')
    list_filter = ('status', 'bill_type', 'due_date', 'created_at')
    search_fields = ('user__email', 'provider_name', 'account_number', 'reference_number')
    readonly_fields = ('id', 'created_at', 'updated_at', 'paid_at', 'reference_number')
    fieldsets = (
        ('Payment Info', {'fields': ('id', 'user', 'bill_type', 'provider_name', 'account_number')}),
        ('Amount & Dates', {'fields': ('amount', 'due_date')}),
        ('Status & Reference', {'fields': ('status', 'reference_number')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'paid_at')}),
    )

    actions = ['mark_as_completed', 'mark_as_failed']

    def mark_as_completed(self, request, queryset):
        queryset.update(status='COMPLETED', paid_at=timezone.now())
        self.message_user(request, f"Marked {queryset.count()} payment(s) as completed.")

    mark_as_completed.short_description = "Mark selected payments as completed"

    def mark_as_failed(self, request, queryset):
        queryset.update(status='FAILED')
        self.message_user(request, f"Marked {queryset.count()} payment(s) as failed.")

    mark_as_failed.short_description = "Mark selected payments as failed"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'title', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('name', 'email', 'title', 'message')
    readonly_fields = ('user', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Reviewer Info', {'fields': ('user', 'name', 'email')}),
        ('Review', {'fields': ('rating', 'title', 'message')}),
        ('Status', {'fields': ('is_approved',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"Approved {queryset.count()} review(s).")
    approve_reviews.short_description = "Approve selected reviews"
    
    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"Disapproved {queryset.count()} review(s).")
    disapprove_reviews.short_description = "Disapprove selected reviews"


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'user', 'transaction_type', 'amount', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('reference_number', 'user__email', 'from_account', 'to_account')
    readonly_fields = ('id', 'reference_number', 'created_at', 'user')
    
    fieldsets = (
        ('Receipt Info', {'fields': ('id', 'reference_number', 'user', 'created_at')}),
        ('Transaction Details', {'fields': ('transaction_type', 'amount', 'description', 'status')}),
        ('Account Info', {'fields': ('from_account', 'to_account', 'recipient_name')}),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False