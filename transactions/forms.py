from django import forms
from .models import Transaction
from accounts.models import UserBankAccount

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type']

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def save(self, commit = True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()

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
                'You cannot withdraw balance that is more than your account balance'
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
        recipient_account_number = self.cleaned_data.get('recipient_account_number')
        recipient_account = UserBankAccount.objects.filter(account_no=recipient_account_number).first()

        if not recipient_account:
            raise forms.ValidationError("Recipient account number is invalid.")
        
        return recipient_account_number
    
    def save(self, commit=True):
        transaction = super().save(commit=False)
        transaction.balance_after_transaction = self.account.balance

        if commit:
            transaction.save()

        return transaction
