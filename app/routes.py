from flask import Blueprint, render_template
from flask import render_template, url_for, flash, redirect,request
from app import db, bcrypt
from app.forms import RegistrationForm, LoginForm
from app.models import User
from flask_login import login_user, current_user, logout_user, login_required
from app.forms import TransactionForm,BudgetForm,FilterForm
from app.models import Transaction,Budget
from flask import redirect, url_for, flash
from flask_login import current_user
from datetime import datetime
from sqlalchemy import func
from datetime import datetime, timedelta
import csv
from flask import Response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import send_file

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import make_response

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
from flask import send_file
from reportlab.lib.units import inch

main = Blueprint('main', __name__)

@main.route('/')
def home():
    logout_user()
    return render_template('index.html')

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.account'))  # Redirect to account page if already authenticated
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login Successful!', 'success')
            return redirect(url_for('main.account'))  # Redirect to account page after successful login
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@main.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    filter_form = FilterForm()

    # Fetch all transactions for the current user
    transactions = Transaction.query.filter_by(user_id=current_user.id)

    # Apply filters if needed
    if filter_form.validate_on_submit():
        if filter_form.category.data != 'All':
            transactions = transactions.filter_by(category=filter_form.category.data)
        if filter_form.start_date.data:
            transactions = transactions.filter(Transaction.date >= filter_form.start_date.data)
        if filter_form.end_date.data:
            transactions = transactions.filter(Transaction.date <= filter_form.end_date.data)

    transactions = transactions.all()

    # Calculate total income, total expenses, and balance
    total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.transaction_type == 'expense')
    balance = total_income - total_expenses

    # Budget and spending logic
    current_month = datetime.now().strftime('%Y-%m')
    budgets = Budget.query.filter_by(user_id=current_user.id, month=current_month).all()
    spending = db.session.query(
        Transaction.category, func.sum(Transaction.amount)
    ).filter(Transaction.user_id == current_user.id, func.strftime('%Y-%m', Transaction.date) == current_month).group_by(Transaction.category).all()
    spending_dict = {category: total for category, total in spending}

    # Budget alerts logic
    budget_alerts = []
    for budget in budgets:
        spent = spending_dict.get(budget.category, 0)
        if spent > budget.amount:
            budget_alerts.append(f"You have exceeded your budget for {budget.category}!")
        elif spent >= 0.9 * budget.amount:
            budget_alerts.append(f"You are close to exceeding your budget for {budget.category}.")

    return render_template('account.html', title='Account', transactions=transactions, budgets=budgets, spending_dict=spending_dict, budget_alerts=budget_alerts, total_income=total_income, total_expenses=total_expenses, balance=balance, form=filter_form)

@main.route("/add_transaction", methods=['GET', 'POST'])
@login_required
def add_transaction():
    form = TransactionForm()
    if form.validate_on_submit():
        transaction = Transaction(
            amount=form.amount.data,
            category=form.category.data,
            date=form.date.data,
            transaction_type=form.transaction_type.data,  # Add the transaction type (income or expense)
            user_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('main.account'))
    return render_template('add_transaction.html', title='Add Transaction', form=form)

@main.route("/transaction/<int:transaction_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Ensure only the owner of the transaction can edit it
    if transaction.user_id != current_user.id:
        flash('You do not have permission to edit this transaction.', 'danger')
        return redirect(url_for('main.account'))
    
    form = TransactionForm()
    
    if form.validate_on_submit():
        # Update the transaction with the new data from the form
        transaction.amount = form.amount.data
        transaction.category = form.category.data
        transaction.date = form.date.data
        print(transaction.amount,transaction.category,transaction.date)
        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('main.account'))
    else:
        print("Form did not validate")
        print(form.amount.data)
        print(form.category.data)
        print(form.date.data)
        print(form.errors)
    
    # Pre-populate the form on GET request
    if request.method == 'GET':
        form.amount.data = transaction.amount
        form.category.data = transaction.category
        form.date.data = transaction.date

    return render_template('edit_transaction.html', form=form)

@main.route("/transaction/<int:transaction_id>/delete", methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.user_id != current_user.id:
        flash('You do not have permission to delete this transaction.', 'danger')
        return redirect(url_for('main.account'))
    
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('main.account'))

@main.route("/budget", methods=['GET', 'POST'])
@login_required
def set_budget():
    form = BudgetForm()
    if form.validate_on_submit():
        budget = Budget(
            category=form.category.data,
            amount=form.amount.data,
            month=form.month.data,
            user_id=current_user.id
        )
        db.session.add(budget)
        db.session.commit()
        flash('Budget set successfully!', 'success')
        return redirect(url_for('main.account'))
    return render_template('set_budget.html', title='Set Budget', form=form)

@main.route("/transactions/filter", methods=['GET', 'POST'])
@login_required
def filter_transactions():
    form = FilterForm()
    transactions = Transaction.query.filter_by(user_id=current_user.id)

    if form.validate_on_submit():
        if form.keyword.data:
            transactions = transactions.filter(Transaction.category.contains(form.keyword.data))
        if form.category.data != 'All':
            transactions = transactions.filter_by(category=form.category.data)
        if form.start_date.data:
            transactions = transactions.filter(Transaction.date >= form.start_date.data)
        if form.end_date.data:
            transactions = transactions.filter(Transaction.date <= form.end_date.data)
        transactions = transactions.all()
    
    return render_template('filter_transactions.html', title='Filter Transactions', form=form, transactions=transactions)


def add_recurring_transactions():
    # Get today's date
    today = datetime.now().date()

    # Get all recurring transactions for the current user
    recurring_transactions = Transaction.query.filter_by(is_recurring=True).all()

    for transaction in recurring_transactions:
        last_transaction_date = transaction.date.date()

        # Calculate the next recurrence date
        if transaction.recurrence_frequency == 'daily':
            next_transaction_date = last_transaction_date + timedelta(days=1)
        elif transaction.recurrence_frequency == 'weekly':
            next_transaction_date = last_transaction_date + timedelta(weeks=1)
        elif transaction.recurrence_frequency == 'monthly':
            next_transaction_date = last_transaction_date + timedelta(weeks=4)

        # If today is the next recurrence date, add a new transaction
        if next_transaction_date <= today:
            new_transaction = Transaction(
                amount=transaction.amount,
                category=transaction.category,
                date=today,
                user_id=transaction.user_id,
                is_recurring=transaction.is_recurring,
                recurrence_frequency=transaction.recurrence_frequency
            )
            db.session.add(new_transaction)
            db.session.commit()



@main.route("/export/csv")
@login_required
def export_transactions_csv():
    # Separate income and expense transactions
    income_transactions = Transaction.query.filter_by(user_id=current_user.id, transaction_type='income').all()
    expense_transactions = Transaction.query.filter_by(user_id=current_user.id, transaction_type='expense').all()

    total_income = sum(t.amount for t in income_transactions)
    total_expenses = sum(t.amount for t in expense_transactions)
    balance = total_income - total_expenses

    # Create a CSV file in memory
    def generate():
        data = []
        
        # Income Section
        data.append('Income Transactions\n')
        data.append('Amount,Category,Date\n')  # CSV headers
        for transaction in income_transactions:
            data.append(f'{transaction.amount},{transaction.category},{transaction.date.strftime("%Y-%m-%d")}\n')

        # Expense Section
        data.append('\nExpense Transactions\n')
        data.append('Amount,Category,Date\n')  # CSV headers
        for transaction in expense_transactions:
            data.append(f'{transaction.amount},{transaction.category},{transaction.date.strftime("%Y-%m-%d")}\n')

        # Summary Section
        data.append('\nSummary\n')
        data.append(f'Total Income,Rs.{total_income:.2f}\n')
        data.append(f'Total Expenses,Rs.{total_expenses:.2f}\n')
        data.append(f'Balance,Rs.{balance:.2f}\n')

        return ''.join(data)

    # Stream the CSV to the client
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=transactions_report.csv"})


@main.route("/export/pdf")
@login_required
def export_transactions_pdf():
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()

    # Create a PDF canvas
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Add title
    c.drawString(100, height - 50, f"Transaction Report for {current_user.username}")

    # Separate income and expense transactions
    income_transactions = Transaction.query.filter_by(user_id=current_user.id, transaction_type='income').all()
    expense_transactions = Transaction.query.filter_by(user_id=current_user.id, transaction_type='expense').all()

    # Define data for income and expenses
    income_data = [['Amount', 'Category', 'Date']]
    expense_data = [['Amount', 'Category', 'Date']]

    total_income = 0
    total_expenses = 0

    # Add income transactions
    for transaction in income_transactions:
        income_data.append([f"{transaction.amount}", f"{transaction.category}", f"{transaction.date.strftime('%Y-%m-%d')}"])
        total_income += transaction.amount

    # Add expense transactions
    for transaction in expense_transactions:
        expense_data.append([f"{transaction.amount}", f"{transaction.category}", f"{transaction.date.strftime('%Y-%m-%d')}"])
        total_expenses += transaction.amount

    balance = total_income - total_expenses

    # Create the income table
    income_table = Table(income_data)
    income_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.green),  # Header background for income
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Create the expense table
    expense_table = Table(expense_data)
    expense_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.red),  # Header background for expenses
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.salmon),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Summary data for income, expenses, and balance
    summary_data = [
        ['Total Income', f"Rs.{total_income:.2f}"],
        ['Total Expenses', f"Rs.{total_expenses:.2f}"],
        ['Balance', f"Rs.{balance:.2f}"]
    ]
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Set positions and add tables to the PDF
    income_table.wrapOn(c, width, height)
    income_table.drawOn(c, 50, height - 150)

    expense_table.wrapOn(c, width, height)
    expense_table.drawOn(c, 50, height - 300)

    summary_table.wrapOn(c, width, height)
    summary_table.drawOn(c, 50, height - 450)

    # Finalize the PDF
    c.showPage()
    c.save()

    # Move buffer to the beginning so we can return it as a response
    buffer.seek(0)

    # Send the PDF as a response
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='transactions_report.pdf')