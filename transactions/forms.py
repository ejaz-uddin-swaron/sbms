from django import forms
from .models import Transaction
from django.db import connection

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type']

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def save(self, commit=True):
        self.instance.account = self.account

        # ✅ fetch latest balance manually
        with connection.cursor() as cursor:
            cursor.execute("SELECT balance FROM accounts_userbankaccount WHERE id = %s", [self.account.id])
            balance = cursor.fetchone()[0]

        self.instance.balance_after_transaction = balance

        return super().save(commit=commit)

class DepositForm(TransactionForm):
    def clean_amount(self):
        min_deposit_amount = 10
        amount = self.cleaned_data.get('amount')
        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} $'
            )
        return amount

class WithdrawForm(TransactionForm):
    def clean_amount(self):
        account = self.account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance
        amount = self.cleaned_data.get('amount')

        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} $'
            )
        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} $'
            )
        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance} $ in your account. '
                'You cannot withdraw more than your current balance'
            )
        return amount

class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount < 1:
            raise forms.ValidationError(
                f'NOOB, you cannot request for negative loans'
            )
        return amount

class SendMoneyForm(TransactionForm):
    recipient_account_number = forms.CharField(max_length=20)

    def clean_amount(self):
        account = self.account
        amount = self.cleaned_data.get('amount')

        if amount < 1:
            raise forms.ValidationError(
                f'NOOB, you cannot transfer negative balance'
            )
        if amount > account.balance:
            raise forms.ValidationError(
                f'NOOB, you cannot send more balance than your current balance'
            )
        return amount

    def clean_recipient_account_number(self):
        from django.db import connection
        recipient_account_number = self.cleaned_data.get('recipient_account_number')
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM accounts_userbankaccount WHERE account_no = %s", [recipient_account_number])
            exists = cursor.fetchone()[0]

        if not exists:
            raise forms.ValidationError("Recipient account number is invalid.")
        return recipient_account_number

    def save(self, commit=True):
        transaction = super().save(commit=False)

        with connection.cursor() as cursor:
            cursor.execute("SELECT balance FROM accounts_userbankaccount WHERE id = %s", [self.account.id])
            balance = cursor.fetchone()[0]

        transaction.balance_after_transaction = balance

        if commit:
            transaction.save()

        return transaction
