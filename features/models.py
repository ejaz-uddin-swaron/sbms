# features/models.py

from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount

User = get_user_model()

# features/models.py

class HajjSavingsAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(UserBankAccount, on_delete=models.CASCADE, null=True, blank=True)  # << add null=True, blank=True
    monthly_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    last_deposit_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.user.username}'s Hajj Savings"
