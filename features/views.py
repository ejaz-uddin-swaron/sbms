from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.

class DonationMoneyView(TemplateView):
    template_name = 'features/donation.html'