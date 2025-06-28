from django.urls import path
from .views import (
    DonationMoneyView,
    QuestionAndAnswerView,
    FAQView,
    create_hajj_savings,
    hajj_savings_dashboard,
    deposit_to_hajj_savings,
)

urlpatterns = [
    path('donation/', DonationMoneyView.as_view(), name='donation'),
    path('QnA/', QuestionAndAnswerView.as_view(), name='QnA'),
    path('FAQ/', FAQView.as_view(), name='FAQ'),

    path('hajj/create/', create_hajj_savings, name='create_hajj_savings'),
    path('hajj/dashboard/', hajj_savings_dashboard, name='hajj_savings_dashboard'),
    path('hajj/deposit/<int:account_id>/', deposit_to_hajj_savings, name='deposit_to_hajj_savings'),
]
