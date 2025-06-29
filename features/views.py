from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import now
from django.db import connection

from .forms import HajjSavingsForm

class DonationMoneyView(TemplateView):
    template_name = 'features/donation.html'

class QuestionAndAnswerView(TemplateView):
    template_name = 'features/question&answer.html'

class FAQView(TemplateView):
    template_name = 'features/FAQ.html'

def fetch_one(sql, params):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
    return row

def fetch_all(sql, params):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    return rows

def execute_sql(sql, params):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)

@login_required
def create_hajj_savings(request):
    if request.method == 'POST':
        form = HajjSavingsForm(request.POST)
        if form.is_valid():
            user_id = request.user.id
            data = form.cleaned_data

            # Check if user has a bank account
            bank_account = fetch_one(
                "SELECT id FROM accounts_userbankaccount WHERE user_id = %s LIMIT 1", [user_id]
            )

            if not bank_account:
                messages.error(request, "No linked bank account found. Please add one first.")
                return redirect('create_hajj_savings')

            account_id = bank_account[0]

            # ✅ Insert into HajjSavingsAccount WITHOUT created_at
            execute_sql("""
                INSERT INTO features_hajjsavingsaccount 
                (user_id, account_id, monthly_deposit, is_active)
                VALUES (%s, %s, %s, TRUE)
            """, [user_id, account_id, data['monthly_deposit']])

            messages.success(request, "Hajj Savings account created successfully.")
            return redirect('hajj_savings_dashboard')
    else:
        form = HajjSavingsForm()

    return render(request, 'features/create_hajj_savings.html', {'form': form})



@login_required
def hajj_savings_dashboard(request):
    user_id = request.user.id
    rows = fetch_all("""
        SELECT id, monthly_deposit, last_deposit_date, is_active 
        FROM features_hajjsavingsaccount 
        WHERE user_id = %s
    """, [user_id])

    savings = [
        {
            'id': row[0],
            'monthly_deposit': row[1],
            'last_deposit_date': row[2],
            'is_active': row[3]
        } for row in rows
    ]

    return render(request, 'features/hajj_savings_dashboard.html', {'savings': savings})


@login_required
def deposit_to_hajj_savings(request, account_id):
    user_id = request.user.id

    # Fetch savings account and validate ownership
    account = fetch_one("""
        SELECT h.id, h.monthly_deposit, h.last_deposit_date, h.is_active,
               b.id as bank_id, b.balance
        FROM features_hajjsavingsaccount h
        JOIN accounts_userbankaccount b ON h.account_id = b.id
        WHERE h.id = %s AND h.user_id = %s
    """, [account_id, user_id])

    if not account:
        messages.error(request, "Savings account not found.")
        return redirect('hajj_savings_dashboard')

    acc_id, monthly_deposit, last_deposit_date, is_active, bank_id, balance = account

    if not is_active:
        messages.error(request, "This savings account is inactive.")
        return redirect('hajj_savings_dashboard')

    if last_deposit_date and last_deposit_date.month == now().month:
        messages.info(request, "Deposit already made this month.")
        return redirect('hajj_savings_dashboard')

    if balance < monthly_deposit:
        messages.error(request, "Insufficient balance in your bank account.")
        return redirect('hajj_savings_dashboard')

    # Deduct from bank account
    execute_sql("""
        UPDATE accounts_userbankaccount 
        SET balance = balance - %s 
        WHERE id = %s
    """, [monthly_deposit, bank_id])

    # Update deposit date
    execute_sql("""
        UPDATE features_hajjsavingsaccount 
        SET last_deposit_date = %s 
        WHERE id = %s
    """, [now().date(), acc_id])

    messages.success(request, f"৳{monthly_deposit} deposited to Hajj Savings.")
    return redirect('hajj_savings_dashboard')
