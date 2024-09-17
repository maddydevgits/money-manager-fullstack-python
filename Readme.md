
# Money Manager

Money Manager is a web-based personal finance management application built using Python Flask. It allows users to track their income, expenses, and savings. With an intuitive interface and detailed reports, users can manage their finances, set budgets, and analyze their spending patterns.

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

Money Manager helps users maintain control over their personal finances by allowing them to:

- Add income and expense transactions.
- Set and monitor budgets for various categories.
- Generate reports that provide a clear breakdown of their financial status over time.

## Features

- **User Authentication**: Secure registration and login.
- **Transaction Management**: Track income and expenses with categorized transactions.
- **Budgeting**: Set monthly or yearly budgets and track how well users are adhering to them.
- **Reports**: Generate monthly and yearly reports with charts.
- **Dashboard**: Overview of financial health including balance, income, and expenses.

## Tech Stack

- **Backend**: Python Flask, SQLAlchemy (ORM)
- **Frontend**: HTML, CSS (Bootstrap), Jinja2 Templating
- **Database**: SQLite (Development), MySQL or PostgreSQL (Production)
- **Authentication**: Flask-Login, bcrypt
- **Charting**: Chart.js for data visualization

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/money-manager.git
cd money-manager
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up the database

- If using SQLite, the database will be created automatically.
- For MySQL/PostgreSQL, update the database URI in `config.py`.

```python
SQLALCHEMY_DATABASE_URI = 'sqlite:///moneymanager.db'
```

### 5. Run the application

```bash
flask run
```

Access the app at `http://127.0.0.1:5000`.

## Usage

- **Register**: Create an account and log in.
- **Dashboard**: View the summary of your financial status.
- **Add Transactions**: Record income and expenses, categorize them.
- **Set Budgets**: Define budgets for specific categories.
- **View Reports**: Analyze monthly and yearly financial trends using graphs.

## API Endpoints

| Method | Endpoint                     | Description                        |
|--------|------------------------------|------------------------------------|
| GET    | `/`                          | Home/Dashboard                     |
| GET    | `/login`                     | Login page                         |
| POST   | `/login`                     | Authenticate user                  |
| GET    | `/register`                  | Register page                      |
| POST   | `/register`                  | Create new user                    |
| GET    | `/transactions`              | View all transactions              |
| POST   | `/transactions`              | Add a new transaction              |
| PUT    | `/transactions/<id>`         | Edit a transaction                 |
| DELETE | `/transactions/<id>`         | Delete a transaction               |
| GET    | `/budget`                    | View budgets                       |
| POST   | `/budget`                    | Set a new budget                   |
| GET    | `/reports`                   | View financial reports             |

## Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository.
2. Create a new branch with your feature/bugfix.
3. Commit your changes and push to your branch.
4. Open a pull request and describe your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
