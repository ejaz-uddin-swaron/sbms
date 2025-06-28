from django.contrib import admin
from .models import HajjSavingsAccount

@admin.register(HajjSavingsAccount)
class HajjSavingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'account', 'monthly_deposit', 'last_deposit_date', 'is_active']

