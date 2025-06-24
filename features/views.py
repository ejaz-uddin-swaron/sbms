from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.

class DonationMoneyView(TemplateView):
    template_name = 'features/donation.html'

# class LoanRequestView(TemplateView):
#     template_name = 'features/loan_req.html'

class QuestionAndAnswerView(TemplateView):
    template_name = 'features/question&answer.html'

class FAQView(TemplateView):
    template_name = 'features/FAQ.html'