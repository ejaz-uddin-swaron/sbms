from django.shortcuts import render
from django.views.generic import TemplateView
import random

# Create your views here.

class homeView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context['x'] = random.randint(1,7)

        return context