from django.contrib.auth.forms import UserCreationForm
from .constants import GENDER, ACCOUNT_TYPE, RELIGION
from django import forms
from django.contrib.auth.models import User
from django.db import connection

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
            account_type = self.cleaned_data.get('account_type')
            gender = self.cleaned_data.get('gender')
            postal_code = self.cleaned_data.get('postal_code')
            country = self.cleaned_data.get('country')
            birth_date = self.cleaned_data.get('birth_date')
            city = self.cleaned_data.get('city')
            street_address = self.cleaned_data.get('street_address')
            religion = self.cleaned_data.get('religion')

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO accounts_useraddress (user_id, street_address, city, postal_code, country)
                    VALUES (%s, %s, %s, %s, %s)
                """, [our_user.id, street_address, city, postal_code, country])

                cursor.execute("""
                    INSERT INTO accounts_userbankaccount 
                    (user_id, account_type, account_no, birth_date, gender, balance, religion, initial_deposit_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
                """, [our_user.id, account_type, 100000 + our_user.id, birth_date, gender, 0, religion])

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

            account_type = self.cleaned_data['account_type']
            gender = self.cleaned_data['gender']
            birth_date = self.cleaned_data['birth_date']
            religion = self.cleaned_data['religion']
            street_address = self.cleaned_data['street_address']
            city = self.cleaned_data['city']
            postal_code = self.cleaned_data['postal_code']
            country = self.cleaned_data['country']

            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM accounts_userbankaccount WHERE user_id = %s", [user.id])
                account = cursor.fetchone()
                if account:
                    cursor.execute("""
                        UPDATE accounts_userbankaccount 
                        SET account_type = %s, gender = %s, birth_date = %s, religion = %s 
                        WHERE user_id = %s
                    """, [account_type, gender, birth_date, religion, user.id])
                else:
                    cursor.execute("""
                        INSERT INTO accounts_userbankaccount 
                        (user_id, account_type, gender, birth_date, religion, account_no, balance, initial_deposit_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
                    """, [user.id, account_type, gender, birth_date, religion, 100000 + user.id, 0])

                cursor.execute("SELECT id FROM accounts_useraddress WHERE user_id = %s", [user.id])
                address = cursor.fetchone()
                if address:
                    cursor.execute("""
                        UPDATE accounts_useraddress 
                        SET street_address = %s, city = %s, postal_code = %s, country = %s 
                        WHERE user_id = %s
                    """, [street_address, city, postal_code, country, user.id])
                else:
                    cursor.execute("""
                        INSERT INTO accounts_useraddress 
                        (user_id, street_address, city, postal_code, country)
                        VALUES (%s, %s, %s, %s, %s)
                    """, [user.id, street_address, city, postal_code, country])

        return user
