from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import DepositForm, WithdrawForm, LoanRequestForm, SendMoneyForm
from .constants import LOAN, LOAN_PAID
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
from django.shortcuts import redirect
from django.views import View
from django.urls import reverse_lazy
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from decimal import Decimal
from accounts.models import UserBankAccount
from .models import Transaction

def send_transaction_email(user, amount, subject, template):
    message = render_to_string(template, {
        'user': user,
        'amount': amount
    })
    send_email = EmailMultiAlternatives(subject, '', to=[user.email])
    send_email.attach_alternative(message, 'text/html')
    send_email.send()

def send_zakat_email(user, amount, zakat_amount, subject, template):
    message = render_to_string(template, {
        'user': user,
        'amount': amount,
        'zakat_amount': zakat_amount
    })
    send_email = EmailMultiAlternatives(subject, '', to=[user.email])
    send_email.attach_alternative(message, 'text/html')
    send_email.send()

class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'account': self.request.user.account})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'title': self.title})
        return context

class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit Money'

    def get_initial(self):
        return {'transaction_type': 1}

    def form_valid(self, form):
        amount = form.cleaned_data['amount']
        user = self.request.user

        account = user.account
        account.balance += amount
        account.save()

        religion = account.religion
        balance = account.balance

        form.instance.balance_after_transaction = balance
        messages.success(self.request, f'{"{:,.2f}".format(float(amount))}$ has been deposited to your account successfully')
        send_transaction_email(user, amount, 'Deposit Email', 'transactions/deposit_email.html')

        if amount >= 588 and religion == 'Islam':
            zakat_amount = amount * Decimal(0.025)
            send_zakat_email(user, amount, zakat_amount, 'Zakat Email', 'transactions/zakat_email.html')

        return super().form_valid(form)

class WithdrawalMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        return {'transaction_type': 2}

    def form_valid(self, form):
        amount = form.cleaned_data['amount']
        user = self.request.user

        account = user.account
        account.balance -= amount
        account.save()

        form.instance.balance_after_transaction = account.balance
        messages.success(self.request, f'{"{:,.2f}".format(float(amount))}$ has been withdrawn from your account')
        send_transaction_email(user, amount, 'Withdrawal Email', 'transactions/withdrawal_email.html')

        return super().form_valid(form)

class LoanRequestMoneyView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        return {'transaction_type': 3}

    def form_valid(self, form):
        user = self.request.user
        loan_count = Transaction.objects.filter(
            account=user.account,
            transaction_type=3,
            loan_approved=True
        ).count()

        if loan_count > 3:
            return HttpResponse('You have crossed your loan request limit')

        amount = form.cleaned_data['amount']
        messages.success(self.request, f'Loan request for {"{:,.2f}".format(float(amount))}$ has been sent to the admin')
        send_transaction_email(user, amount, 'Loan Request', 'transactions/loan_request_email.html')
        return super().form_valid(form)

class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    context_object_name = 'report_list'

    def get_queryset(self):
        account_id = self.request.user.account.id
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        raw_queryset = Transaction.objects.filter(account_id=account_id)

        if start_date and end_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            raw_queryset = raw_queryset.filter(timestamp__date__gte=start, timestamp__date__lte=end)

        return raw_queryset.order_by('-timestamp').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'account': self.request.user.account})
        return context

class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        try:
            loan = Transaction.objects.get(id=loan_id)
        except Transaction.DoesNotExist:
            messages.error(request, "Loan not found.")
            return redirect('loan_list')

        if not loan.loan_approved:
            messages.error(request, "Loan not approved yet.")
            return redirect('loan_list')

        account = loan.account
        if loan.amount > account.balance:
            messages.error(request, f'Loan amount exceeds available balance')
            return redirect('loan_list')

        account.balance -= loan.amount
        account.save()

        loan.transaction_type = LOAN_PAID
        loan.balance_after_transaction = account.balance
        loan.save()

        return redirect('loan_list')

class LoanListView(LoginRequiredMixin, ListView):
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'

    def get_queryset(self):
        return Transaction.objects.filter(
            account=self.request.user.account,
            transaction_type=LOAN
        )

class SendMoneyView(TransactionCreateMixin):
    form_class = SendMoneyForm
    template_name = 'transactions/transaction_form.html'
    title = 'Send Money'
    success_url = reverse_lazy('transaction_report')

    def get_initial(self):
        return {'transaction_type': 5}

    def form_valid(self, form):
        amount = form.cleaned_data['amount']
        recipient_account_number = form.cleaned_data['recipient_account_number']
        user = self.request.user

        try:
            recipient_account = UserBankAccount.objects.get(account_no=recipient_account_number)
        except UserBankAccount.DoesNotExist:
            messages.error(self.request, "Recipient not found.")
            return redirect('transaction_report')

        sender_account = user.account

        sender_account.balance -= amount
        recipient_account.balance += amount

        sender_account.save()
        recipient_account.save()

        form.instance.balance_after_transaction = sender_account.balance
        transaction = form.save(commit=False)
        transaction.save()

        messages.success(self.request, f'Successfully sent {"{:,.2f}".format(float(amount))}$ to recipient.')
        send_transaction_email(user, amount, 'Send Money Email', 'transactions/send_money_email.html')

        from django.contrib.auth.models import User
        recipient_user = User.objects.get(id=recipient_account.user.id)
        send_transaction_email(recipient_user, amount, 'Money Received Email', 'transactions/receive_money_email.html')

        return super().form_valid(form)
