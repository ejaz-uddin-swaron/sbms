from django.shortcuts import render, redirect
from django.views.generic import FormView
from .forms import UserRegistrationForm, UserUpdateForm
from django.contrib.auth import login, logout
from django.views import View
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from .models import UserBankAccount, UserAddress 

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

    def get_initial_data(self, user):
        data = {}

        try:
            account = UserBankAccount.objects.get(user=user)
            data.update({
                'account_type': account.account_type,
                'gender': account.gender,
                'birth_date': account.birth_date,
                'religion': account.religion
            })
        except UserBankAccount.DoesNotExist:
            pass

        try:
            address = UserAddress.objects.get(user=user)
            data.update({
                'street_address': address.street_address,
                'city': address.city,
                'postal_code': address.postal_code,
                'country': address.country
            })
        except UserAddress.DoesNotExist:
            pass

        return data

    def get(self, request):
        initial = self.get_initial_data(request.user)
        form = UserUpdateForm(instance=request.user, initial=initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
        return render(request, self.template_name, {'form': form})
