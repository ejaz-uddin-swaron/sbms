from django import forms
from .models import HajjSavingsAccount

class HajjSavingsForm(forms.ModelForm):
    class Meta:
        model = HajjSavingsAccount
        fields = ['monthly_deposit']
