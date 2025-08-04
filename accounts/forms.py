from django.contrib.auth.forms import UserCreationForm
from .constants import GENDER, ACCOUNT_TYPE, RELIGION
from django import forms
from django.contrib.auth.models import User
from accounts.models import UserBankAccount, UserAddress

class UserRegistrationForm(UserCreationForm):
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    gender = forms.ChoiceField(choices=GENDER)
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPE)
    street_address = forms.CharField(max_length=100)
    city = forms.CharField(max_length=100)
    postal_code = forms.IntegerField()
    country = forms.CharField(max_length=100)
    religion = forms.ChoiceField(choices=RELIGION)

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'account_type', 'birth_date', 'gender', 'postal_code', 'city', 'country', 'street_address', 'religion']

    def save(self, commit=True):
        our_user = super().save(commit=False)

        if commit:
            our_user.save()
            UserAddress.objects.create(
                user=our_user,
                street_address=self.cleaned_data.get('street_address'),
                city=self.cleaned_data.get('city'),
                postal_code=self.cleaned_data.get('postal_code'),
                country=self.cleaned_data.get('country'),
            )
            UserBankAccount.objects.create(
                user=our_user,
                account_type=self.cleaned_data.get('account_type'),
                account_no=100000 + our_user.id,
                birth_date=self.cleaned_data.get('birth_date'),
                gender=self.cleaned_data.get('gender'),
                balance=0,
                religion=self.cleaned_data.get('religion'),
            )

        return our_user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'appearance-none block w-full bg-gray-200 '
                    'text-gray-700 border border-gray-200 rounded '
                    'py-3 px-4 leading-tight focus:outline-none '
                    'focus:bg-white focus:border-gray-500'
                )
            })


class UserUpdateForm(forms.ModelForm):
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    gender = forms.ChoiceField(choices=GENDER)
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPE)
    street_address = forms.CharField(max_length=100)
    city = forms.CharField(max_length= 100)
    postal_code = forms.IntegerField()
    country = forms.CharField(max_length=100)
    religion = forms.ChoiceField(choices=RELIGION)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'appearance-none block w-full bg-gray-200 '
                    'text-gray-700 border border-gray-200 rounded '
                    'py-3 px-4 leading-tight focus:outline-none '
                    'focus:bg-white focus:border-gray-500'
                )
            })

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()

            account_data = {
                'account_type': self.cleaned_data['account_type'],
                'gender': self.cleaned_data['gender'],
                'birth_date': self.cleaned_data['birth_date'],
                'religion': self.cleaned_data['religion'],
            }

            account, created = UserBankAccount.objects.get_or_create(user=user, defaults={
                **account_data,
                'account_no': 100000 + user.id,
                'balance': 0,
            })
            if not created:
                for field, value in account_data.items():
                    setattr(account, field, value)
                account.save()

            address_data = {
                'street_address': self.cleaned_data['street_address'],
                'city': self.cleaned_data['city'],
                'postal_code': self.cleaned_data['postal_code'],
                'country': self.cleaned_data['country'],
            }

            address, created = UserAddress.objects.get_or_create(user=user, defaults=address_data)
            if not created:
                for field, value in address_data.items():
                    setattr(address, field, value)
                address.save()

        return user
