<img align="center" height="200" alt="CoinTrace Banner" title="CoinTrace" src="https://i.imgur.com/0Np8SdO.png"/>

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/python-%233670A0.svg?style=for-the-badge&logo=python&logoColor=ffdd54)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/sqlalchemy-%23D71F00.svg?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Alembic](https://img.shields.io/badge/alembic-%cfcb0a.svg?style=for-the-badge&logoColor=white)
![FastAPI](https://img.shields.io/badge/fastapi-%23009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)

# CoinTrace

Personal finance REST API to track your transactions, accounts, expenses, and credit installments. The focus here is to be a microservice to register simple personal finance.

## Features

- **Transactions** — create, update, delete, list debit/credit transactions; bulk import via `.xlsx`, `.xls`, or `.ofx` files
- **Bank Accounts** — manage multiple accounts (checking, savings, etc.) with an opening balance
- **Fixed Expenses** — register recurring monthly expenses with a due day and optional linked account
- **Credit Installments** — automatic installment breakdown from credit transactions, with optional interest rate
- **Banks** — pre-seeded list of Brazilian banks

## Tech Stack

- **Runtime:** Python 3.13
- **Framework:** FastAPI
- **Database:** PostgreSQL 16
- **ORM:** SQLAlchemy 2 (mapped dataclasses)
- **Migrations:** Alembic
- **Validation:** Pydantic v2
- **Containers:** Docker + Docker Compose

## Getting Started

### With Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

The API will be available at `http://localhost:8000`.

### Locally

**Prerequisites:** Python 3.13, PostgreSQL

it is recommended to create a local env

```bash
python -m venv venv
./venv/scripts/activate
pip install -r requirements.txt
```

with the requirements installed you will need use:

```bash
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
| `PROD` | Disable some public info | `False` |
| `LOCAL` | Automatically modifies the Database url to runs on localhost, if you will use in docker mantain False, otherwise set True | `False` |
| `DEMO` | If enable it'll upload mockup data on a Demo Database and POST, PATCH, DELETE, PUT it won't work  | `False` |

See [.env.example](.env.example) for a full template.

## API Documentation

After starting the server, open:

- # in work

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
