from django.urls import path
from .views import DonationMoneyView

urlpatterns = [
    path('donation/', DonationMoneyView.as_view(), name='donation'),
    # path('loan_request/',),
    # path('QnA/', ),
]