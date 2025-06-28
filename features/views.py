from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import now

from .models import HajjSavingsAccount
from .forms import HajjSavingsForm
from accounts.models import UserBankAccount

# Your original DonationMoneyView
class DonationMoneyView(TemplateView):
    template_name = 'features/donation.html'

class QuestionAndAnswerView(TemplateView):
    template_name = 'features/question&answer.html'

class FAQView(TemplateView):
    template_name = 'features/FAQ.html'

@login_required
def create_hajj_savings(request):
    if request.method == 'POST':
        form = HajjSavingsForm(request.POST)
        if form.is_valid():
            hajj_savings = form.save(commit=False)
            hajj_savings.user = request.user
            # Assign default bank account or logic to select user's bank account
            user_bank_account = UserBankAccount.objects.filter(user=request.user).first()
            if not user_bank_account:
                messages.error(request, "No linked bank account found. Please add one first.")
                return redirect('create_hajj_savings')
            hajj_savings.account = user_bank_account
            hajj_savings.save()
            messages.success(request, "Hajj Savings account created successfully.")
            return redirect('hajj_savings_dashboard')
    else:
        form = HajjSavingsForm()
    return render(request, 'features/create_hajj_savings.html', {'form': form})

@login_required
def hajj_savings_dashboard(request):
    accounts = HajjSavingsAccount.objects.filter(user=request.user)
    return render(request, 'features/hajj_savings_dashboard.html', {'savings': accounts})

@login_required
def deposit_to_hajj_savings(request, account_id):
    account = get_object_or_404(HajjSavingsAccount, id=account_id, user=request.user)

    if not account.is_active:
        messages.error(request, "This savings account is inactive.")
        return redirect('hajj_savings_dashboard')

    if account.last_deposit_date and account.last_deposit_date.month == now().month:
        messages.info(request, "Deposit already made this month.")
        return redirect('hajj_savings_dashboard')

    if account.account.balance < account.monthly_deposit:
        messages.error(request, "Insufficient balance in your bank account.")
        return redirect('hajj_savings_dashboard')

    # Deduct & Save
    account.account.balance -= account.monthly_deposit
    account.account.save()

    account.last_deposit_date = now().date()
    account.save()

    messages.success(request, f"৳{account.monthly_deposit} deposited to Hajj Savings.")
    return redirect('hajj_savings_dashboard')
