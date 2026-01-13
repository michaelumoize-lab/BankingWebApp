from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('transfer/', views.transfer_view, name='transfer'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('api/notification/<str:notification_id>/mark-read/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('card/pay-fee/', views.pay_card_fee, name='pay_card_fee'),
    path('card/view/', views.view_debit_card, name='view_debit_card'),
    path('card/apply/', views.apply_for_card, name='apply_for_card'),
    
    # Loan URLs
    path('loan/apply/', views.apply_for_loan, name='apply_for_loan'),
    path('loan/applications/', views.loan_applications_list, name='loan_applications'),
    path('loan/<uuid:loan_id>/', views.loan_detail, name='loan_detail'),
    
    # Bank Statement URLs
    path('statement/request/', views.request_bank_statement, name='request_bank_statement'),
    path('statements/', views.bank_statements_list, name='bank_statements'),
    
    # Bill Payment URLs
    path('bill/pay/', views.pay_bill, name='pay_bill'),
    path('bills/', views.bill_payments_list, name='bill_payments'),
    
    # Receipt URLs
    path('receipt/<uuid:receipt_id>/', views.receipt_view, name='receipt_view'),
    path('receipts/', views.receipts_list, name='receipts_list'),
]

