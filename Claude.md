# CLAUDE.md - financial-api

## Project Overview

This is a microservice to control personal finances, it won't have a frontend, just a API Restful.

## Core Functions

- **Control transactions (building)**: It capable to upload the transactions made by the user 
- **Control month expanses (building)**: It capable to register and fixed espanses that must be payed every month
- **Control actually money avaliable in account**: Register how much the user expend in which of their accounts.
- **Register any accounts**: It capable to separe the money from diverses sources  

## Tech Stack

- **Database:** PostgreeSQL 4
- **Backend:** Python 3.13, SQLalchemy, swagger, alembic, fastapi

## Code Quality

- **Early Returns**: Use to avoid nested conditions
- **Descriptive Names**: Use clear variable/function names (prefix handlers with "handle")
- **DRY Code**: Don't repeat yourself
- **Functional Style**: Prefer functional, immutable approaches when not verbose
- **Minimal Changes**: Only modify code related to the task at hand
- **Function Ordering**: Define composing functions before their components
- **Simplicity**: Prioritize simplicity and readability over clever solutions
- **Build Iteratively** Start with minimal functionality and verify it works before adding complexity
- **Run Tests**: Test your code frequently with realistic inputs and validate outputs
- **Build Test Environments**: Create testing environments for components that are difficult to validate directly
- **Functional Code**: Use functional and stateless approaches where they improve clarity
- **Clean logic**: Keep core logic clean and push implementation details to the edges
- **File Organsiation**: Balance file organization with simplicity - use an appropriate number of files for the project scale

## project structure


│   ├── .claude/
│   │   └── settings.local.json
│   ├── alembic/ **Database Migrations**
│   ├── app/ **Main application**
│   │   └── main.py **Fast API init**
│   │   ├── api/ **API Routes**
│   │   │   ├── v1/
│   │   │   │   └── router.py
│   │   │   │   ├── routes/
│   │   │   │   │   ├── banks.py **table avaliable bank options to register in transactions and bank_accounts**
│   │   │   │   │   ├── bank_accounts.py **table users' bank_accounts**
│   │   │   │   │   └── transactions.py **table users' transactions**
│   │   │   │   │   ├── account_balances.py **view account balance**
│   │   │   │   │   ├── credit_installments.py **view credit installments from transactions**
│   │   │   │   │   └── fixed_expenses.py **table users' fixed expenses**
│   │   ├── constants/ **Demo dataset**
│   │   ├── core/ **Core config and database**
│   │   │   ├── config.py **ignore**
│   │   │   ├── database.py **database connection**
│   │   │   └── demo_seed.py **insert demo dataset in database**
│   │   ├── models/ **Postgreesql Models**
│   │   │   └── models.py **banks, transactions and bank_accounts models**
│   │   ├── repositories/ **Endpoints logic**
│   │   │   ├── account_balances.py
│   │   │   ├── banks.py
│   │   │   ├── bank_accounts.py
│   │   │   ├── credit_installments.py
│   │   │   ├── fixed_expenses.py
│   │   │   └── transactions.py
│   │   ├── schemas/ **Swagger & Pydentic documentation**
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── account_balances.py
│   │   │   ├── banks.py
│   │   │   ├── bank_accounts.py
│   │   │   ├── credit_installments.py
│   │   │   ├── fixed_expenses.py
│   │   │   └── transactions.py
│   ├── tests/ **pytest**
│   │   └── conftest.py

## Setup

Activate the conda environment (dependencies already installed):

```bash
conda activate financial-control
```

Copy environment variables:

```bash
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/api/v1/docs

## Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "message"
```

Apply migrations:   

```bash
alembic upgrade head
```

## Tests

```bash
pytest
```
