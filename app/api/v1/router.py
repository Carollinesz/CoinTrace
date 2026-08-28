from fastapi import APIRouter

from app.api.v1.routes import bank_accounts, banks, fixed_expenses, transactions

api_router = APIRouter()
api_router.include_router(bank_accounts.router)
api_router.include_router(banks.router)
api_router.include_router(transactions.router)
api_router.include_router(fixed_expenses.router)

