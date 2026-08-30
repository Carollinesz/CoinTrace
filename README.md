# CoinTrace

Personal finance REST API to track your transactions, accounts, expensess, and credit installments. 

## Features

- **Transactions** — create, update, delete, list debit/credit transactions; bulk import via `.xlsx`, `.xls`, or `.ofx` files
- **Bank Accounts** — manage multiple accounts (checking, savings, etc.) with an opening balance
- **Fixed Expenses** — register recurring monthly expenses with a due day and optional linked account
- **Credit Installments** — automatic installment breakdown from credit transactions, with optional interest rate
- **Account Balances** — real-time balance view per account (start value + gains − expenses)
- **Banks** — pre-seeded list of Brazilian banks

## Tech Stack

- **Runtime:** Python 3.13
- **Framework:** FastAPI
- **Database:** PostgreSQL 16
- **ORM:** SQLAlchemy 2 (mapped dataclasses)
- **Migrations:** Alembic
- **Validation:** Pydantic v2
- **Docs:** Swagger UI / ReDoc (auto-generated)
- **Containers:** Docker + Docker Compose

## Getting Started

### With Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

The API will be available at `http://localhost:8000`.

### Locally

**Prerequisites:** Python 3.13, PostgreSQL, conda

```bash
conda activate financial-control
cp .env.example .env
# edit .env with your database credentials
alembic upgrade head
uvicorn app.main:app --reload
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string for the app | — |
| `MIGRATION_DATABASE_URL` | SQLAlchemy connection string for Alembic (superuser) | — |
| `POSTGRES_USER` | PostgreSQL superuser (Docker) | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL superuser password (Docker) | `postgres` |
| `USERNAME_API` | App database user | `user` |
| `USERNAME_PASSWORD` | App database user password | `123` |
| `DB_PORT` | Database port | `5432` |
| `DEBUG` | Enable debug mode | `False` |

See [.env.example](.env.example) for a full template.

## API Documentation

After starting the server, open:

- **Swagger UI:** `http://localhost:8000/api/v1/docs`
- **ReDoc:** `http://localhost:8000/api/v1/redoc`

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/transactions` | List transactions |
| `POST` | `/api/v1/transactions` | Create a transaction |
| `POST` | `/api/v1/transactions/upload` | Bulk import (xlsx/xls/ofx) |
| `PATCH` | `/api/v1/transactions/{id}` | Update a transaction |
| `DELETE` | `/api/v1/transactions/{id}` | Delete a transaction |
| `GET` | `/api/v1/bank-accounts` | List bank accounts |
| `POST` | `/api/v1/bank-accounts` | Create a bank account |
| `PATCH` | `/api/v1/bank-accounts/{id}` | Update a bank account |
| `DELETE` | `/api/v1/bank-accounts/{id}` | Delete a bank account |
| `GET` | `/api/v1/fixed-expenses` | List fixed expenses |
| `POST` | `/api/v1/fixed-expenses` | Create a fixed expense |
| `PATCH` | `/api/v1/fixed-expenses/{id}` | Update a fixed expense |
| `DELETE` | `/api/v1/fixed-expenses/{id}` | Delete a fixed expense |
| `GET` | `/api/v1/account-balances` | View balances per account |
| `GET` | `/api/v1/transactions/credit-installments` | View credit installment breakdown |
| `GET` | `/api/v1/banks` | List available banks |
| `GET` | `/health` | Health check |

## Credit Transactions

Credit purchases support installments and optional monthly interest. Pass a `details` object when creating a credit transaction:

```json
{
  "type": "credit",
  "value": -1200.00,
  "transaction_date": "2026-05-01",
  "description": "New laptop",
  "details": {
    "installments": 12,
    "first_payment": "2026-06-10",
    "interest": 0.0199
  }
}
```

The `credit_installments` view automatically calculates each installment's due date and value.

## Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head
```

## Tests

```bash
pytest
```
