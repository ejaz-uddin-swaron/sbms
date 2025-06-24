from django.urls import path
from .views import DepositMoneyView, WithdrawalMoneyView, TransactionReportView, LoanRequestMoneyView, LoanListView, PayLoanView, SendMoneyView

urlpatterns = [
    path('deposit/', DepositMoneyView.as_view(), name='deposit_money'),
    path('report/', TransactionReportView.as_view(), name='transaction_report'),
    path('withdraw/', WithdrawalMoneyView.as_view(), name='withdraw_money'),
    path('loan_request/', LoanRequestMoneyView.as_view(), name='loan_request'),
    path('loans/', LoanListView.as_view(), name='loan_list'),
    path('loan/<int:loan_id>', PayLoanView.as_view(), name='loan_pay'),
    path('send_money/', SendMoneyView.as_view(), name='send_money'),
]