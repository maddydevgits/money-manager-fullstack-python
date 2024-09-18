from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError,Optional
from app.models import User
from wtforms import FloatField, DateField, SelectField
from wtforms import BooleanField, SelectField

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class TransactionForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    category = SelectField('Category', choices=[('Food', 'Food'), ('Rent', 'Rent'), ('Salary', 'Salary'), ('Other', 'Other')], validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    
    # Fields for recurring transactions
    is_recurring = BooleanField('Recurring')
    recurrence_frequency = SelectField('Recurrence Frequency', choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], validators=[Optional()])
    
    submit = SubmitField('Add Transaction')

class BudgetForm(FlaskForm):
    category = SelectField('Category', choices=[('Food', 'Food'), ('Rent', 'Rent'), ('Salary', 'Salary'), ('Other', 'Other')], validators=[DataRequired()])
    amount = FloatField('Budget Amount', validators=[DataRequired()])
    month = StringField('Month (YYYY-MM)', validators=[DataRequired()])
    submit = SubmitField('Set Budget')

class FilterForm(FlaskForm):
    keyword = StringField('Keyword')
    category = SelectField('Category', choices=[('All', 'All'), ('Food', 'Food'), ('Rent', 'Rent'), ('Salary', 'Salary'), ('Other', 'Other')], validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d')
    end_date = DateField('End Date', format='%Y-%m-%d')
    submit = SubmitField('Filter')