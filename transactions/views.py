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
from django.db import connection
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

        with connection.cursor() as cursor:
            cursor.execute("UPDATE accounts_userbankaccount SET balance = balance + %s WHERE user_id = %s", [amount, user.id])
            cursor.execute("SELECT religion, balance FROM accounts_userbankaccount WHERE user_id = %s", [user.id])
            religion, balance = cursor.fetchone()

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

        with connection.cursor() as cursor:
            cursor.execute("UPDATE accounts_userbankaccount SET balance = balance - %s WHERE user_id = %s", [amount, user.id])
            cursor.execute("SELECT balance FROM accounts_userbankaccount WHERE user_id = %s", [user.id])
            balance = cursor.fetchone()[0]

        form.instance.balance_after_transaction = balance
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
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM transactions_transaction 
                WHERE account_id = (SELECT id FROM accounts_userbankaccount WHERE user_id = %s) 
                AND transaction_type = 3 AND loan_approved = TRUE
            """, [user.id])
            loan_count = cursor.fetchone()[0]

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
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, amount, account_id, loan_approved FROM transactions_transaction WHERE id = %s", [loan_id])
            loan = cursor.fetchone()
            if not loan:
                messages.error(request, "Loan not found.")
                return redirect('loan_list')

            loan_id, amount, account_id, approved = loan
            if not approved:
                messages.error(request, "Loan not approved yet.")
                return redirect('loan_list')

            cursor.execute("SELECT balance FROM accounts_userbankaccount WHERE id = %s", [account_id])
            balance = cursor.fetchone()[0]

            if amount > balance:
                messages.error(request, f'Loan amount exceeds available balance')
                return redirect('loan_list')

            new_balance = balance - amount

            cursor.execute("UPDATE accounts_userbankaccount SET balance = %s WHERE id = %s", [new_balance, account_id])
            cursor.execute("""
                UPDATE transactions_transaction 
                SET transaction_type = %s, balance_after_transaction = %s 
                WHERE id = %s
            """, [LOAN_PAID, new_balance, loan_id])

        return redirect('loan_list')

class LoanListView(LoginRequiredMixin, ListView):
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'

    def get_queryset(self):
        return Transaction.objects.raw("""
            SELECT * FROM transactions_transaction 
            WHERE account_id = %s AND transaction_type = %s
        """, [self.request.user.account.id, LOAN])

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

        with connection.cursor() as cursor:
            cursor.execute("SELECT id, user_id, balance FROM accounts_userbankaccount WHERE account_no = %s", [recipient_account_number])
            recipient = cursor.fetchone()
            if not recipient:
                messages.error(self.request, "Recipient not found.")
                return redirect('transaction_report')

            recipient_id, recipient_user_id, recipient_balance = recipient

            cursor.execute("SELECT id, balance FROM accounts_userbankaccount WHERE user_id = %s", [user.id])
            sender_id, sender_balance = cursor.fetchone()

            new_sender_balance = sender_balance - amount
            new_recipient_balance = recipient_balance + amount

            cursor.execute("UPDATE accounts_userbankaccount SET balance = %s WHERE id = %s", [new_sender_balance, sender_id])
            cursor.execute("UPDATE accounts_userbankaccount SET balance = %s WHERE id = %s", [new_recipient_balance, recipient_id])

        form.instance.balance_after_transaction = new_sender_balance
        transaction = form.save(commit=False)
        transaction.save()

        messages.success(self.request, f'Successfully sent {"{:,.2f}".format(float(amount))}$ to recipient.')
        send_transaction_email(user, amount, 'Send Money Email', 'transactions/send_money_email.html')

        from django.contrib.auth.models import User  
        recipient_user = User.objects.get(id=recipient_user_id)
        send_transaction_email(recipient_user, amount, 'Money Received Email', 'transactions/receive_money_email.html')

        return super().form_valid(form)
