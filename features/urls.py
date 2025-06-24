from django.urls import path
from .views import DonationMoneyView, QuestionAndAnswerView, FAQView

urlpatterns = [
    path('donation/', DonationMoneyView.as_view(), name='donation'),
    path('QnA/', QuestionAndAnswerView.as_view(), name='QnA'),
    path('FAQ/', FAQView.as_view(), name='FAQ')
]