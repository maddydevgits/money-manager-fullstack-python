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

@main.route("/account")
@login_required
def account():
    # Call the recurring transaction function
    add_recurring_transactions()

    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    
    # Get the current month
    current_month = datetime.now().strftime('%Y-%m')
    
    # Fetch user's budgets for the current month
    budgets = Budget.query.filter_by(user_id=current_user.id, month=current_month).all()
    
    # Calculate the total spent per category
    spending = db.session.query(
        Transaction.category, func.sum(Transaction.amount)
    ).filter(Transaction.user_id == current_user.id, func.strftime('%Y-%m', Transaction.date) == current_month).group_by(Transaction.category).all()
    
    # Map the spending to a dictionary
    spending_dict = {category: total for category, total in spending}
    
    # Check for budget alerts
    budget_alerts = []
    for budget in budgets:
        spent = spending_dict.get(budget.category, 0)
        if spent > budget.amount:
            budget_alerts.append(f"You have exceeded your budget for {budget.category}!")
        elif spent >= 0.9 * budget.amount:  # Alert if 90% of the budget is spent
            budget_alerts.append(f"You are close to exceeding your budget for {budget.category}.")
    
    return render_template('account.html', title='Account', transactions=transactions, budgets=budgets, spending_dict=spending_dict, budget_alerts=budget_alerts)

@main.route("/add_transaction", methods=['GET', 'POST'])
@login_required
def add_transaction():
    form = TransactionForm()
    if form.validate_on_submit():
        transaction = Transaction(
            amount=form.amount.data,
            category=form.category.data,
            date=form.date.data,
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
    if transaction.user_id != current_user.id:
        flash('You do not have permission to edit this transaction.', 'danger')
        return redirect(url_for('main.account'))
    
    form = TransactionForm()
    if form.validate_on_submit():
        transaction.amount = form.amount.data
        transaction.category = form.category.data
        transaction.date = form.date.data
        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('main.account'))
    
    elif request.method == 'GET':
        form.amount.data = transaction.amount
        form.category.data = transaction.category
        form.date.data = transaction.date
    
    return render_template('edit_transaction.html', title='Edit Transaction', form=form)

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
            transactions = transactions.filter(Transaction.description.contains(form.keyword.data))
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
    # Get the current user's transactions
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    # Create a CSV file in memory
    def generate():
        data = ['Amount,Category,Date\n']  # CSV headers
        for transaction in transactions:
            data.append(f'{transaction.amount},{transaction.category},{transaction.date.strftime("%Y-%m-%d")}\n')
        return data

    # Stream the CSV to the client
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=transactions.csv"})



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

    # Define transaction data for the table (with headers)
    data = [['Amount', 'Category', 'Date']]
    
    # Add transaction data
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    for transaction in transactions:
        data.append([f"{transaction.amount}", f"{transaction.category}", f"{transaction.date.strftime('%Y-%m-%d')}"])

    # Create the table with the data
    table = Table(data)

    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Header background color
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center align text
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold header font
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Padding for header
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Background color for rows
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines between cells
    ]))

    # Set the table's position
    table.wrapOn(c, width, height)
    table.drawOn(c, 50, height - 200)  # Draw the table on the PDF at a specified position

    # Finalize the PDF
    c.showPage()
    c.save()

    # Move buffer to the beginning so we can return it as a response
    buffer.seek(0)

    # Send the PDF as a response
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='transactions.pdf')