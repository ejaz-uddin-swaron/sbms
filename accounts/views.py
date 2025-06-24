from django.shortcuts import render, redirect
from django.views.generic import FormView
from .forms import UserRegistrationForm, UserUpdateForm
from django.contrib.auth import login, logout
from django.views import View
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.db import connection
from django.contrib.auth.models import User

class UserRegistrationView(FormView):
    template_name = 'accounts/user_registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'
    def get_success_url(self):
        return reverse_lazy('home')

class UserLogoutView(LogoutView):
    def get_success_url(self):
        if self.request.user.is_authenticated:
            logout(self.request)
        return reverse_lazy('home')

class UserBankAccountUpdateView(View):
    template_name = 'accounts/profile.html'

    def get_initial_data(self, user_id):
        data = {}
        with connection.cursor() as cursor:
            cursor.execute("SELECT account_type, gender, birth_date, religion FROM accounts_userbankaccount WHERE user_id = %s", [user_id])
            account = cursor.fetchone()
            if account:
                data['account_type'], data['gender'], data['birth_date'], data['religion'] = account

            cursor.execute("SELECT street_address, city, postal_code, country FROM accounts_useraddress WHERE user_id = %s", [user_id])
            address = cursor.fetchone()
            if address:
                data['street_address'], data['city'], data['postal_code'], data['country'] = address
        return data

    def get(self, request):
        initial = self.get_initial_data(request.user.id)
        form = UserUpdateForm(instance=request.user, initial=initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
        return render(request, self.template_name, {'form': form})
