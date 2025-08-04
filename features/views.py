from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import now

from .forms import HajjSavingsForm
from accounts.models import UserBankAccount
from .models import HajjSavingsAccount

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
            user = request.user
            data = form.cleaned_data

            try:
                bank_account = UserBankAccount.objects.get(user=user)
            except UserBankAccount.DoesNotExist:
                messages.error(request, "No linked bank account found. Please add one first.")
                return redirect('create_hajj_savings')

            HajjSavingsAccount.objects.create(
                user=user,
                account=bank_account,
                monthly_deposit=data['monthly_deposit'],
                is_active=True
            )

            messages.success(request, "Hajj Savings account created successfully.")
            return redirect('hajj_savings_dashboard')
    else:
        form = HajjSavingsForm()

    return render(request, 'features/create_hajj_savings.html', {'form': form})


@login_required
def hajj_savings_dashboard(request):
    savings_accounts = HajjSavingsAccount.objects.filter(user=request.user)
    savings = [
        {
            'id': s.id,
            'monthly_deposit': s.monthly_deposit,
            'last_deposit_date': s.last_deposit_date,
            'is_active': s.is_active
        } for s in savings_accounts
    ]
    return render(request, 'features/hajj_savings_dashboard.html', {'savings': savings})


@login_required
def deposit_to_hajj_savings(request, account_id):
    user = request.user
    try:
        savings_account = HajjSavingsAccount.objects.select_related('account').get(id=account_id, user=user)
    except HajjSavingsAccount.DoesNotExist:
        messages.error(request, "Savings account not found.")
        return redirect('hajj_savings_dashboard')

    if not savings_account.is_active:
        messages.error(request, "This savings account is inactive.")
        return redirect('hajj_savings_dashboard')

    if savings_account.last_deposit_date and savings_account.last_deposit_date.month == now().month:
        messages.info(request, "Deposit already made this month.")
        return redirect('hajj_savings_dashboard')

    bank_account = savings_account.account
    if bank_account.balance < savings_account.monthly_deposit:
        messages.error(request, "Insufficient balance in your bank account.")
        return redirect('hajj_savings_dashboard')

    bank_account.balance -= savings_account.monthly_deposit
    bank_account.save()

    savings_account.last_deposit_date = now().date()
    savings_account.save()

    messages.success(request, f"৳{savings_account.monthly_deposit} deposited to Hajj Savings.")
    return redirect('hajj_savings_dashboard')
