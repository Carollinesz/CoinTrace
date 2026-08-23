financial_control — Overview
Versão: v1 | Base URL: http://localhost:8000/api/v1/
No auth required yet.

Pagination: All get endpoints accepts skip and limit 
Currency: All currency in accepts until 4 digits of precision, ex: 10.1000 = R$ 10,10
Responses: Always in JSON { data, meta, errors }

Status code in common use

## bank-accounts

GET /bank-accounts — Handle list the user's bank accounts
GET /bank-accounts/{account_id} — Handle list a expecific bank account
POST /bank-accounts — Handle create a new bank accounts
PATCH /bank-accounts/{account_id} — Handle Update a bank account
DELETE /bank-accounts/{account_id} —Handle Delete a bank account

## banks

GET /banks — Handle list the avaliable banks that the user can associate the account 
GET /banks/{bank_id}  — Handle list a expecific bank

## Transactions

GET /transactions — Handle list all transactions in all accounts
GET /transactions/{transaction_id} — Handle list a expecific transaction
POST /transactions — Handle create a new transaction (must be associated in a account. But the account_id is not a foreing key more explanation in references/endpoint.md)
PATCH /transactions/{transaction_id} — Handle Update a transaction 
DELETE /transactions/{transaction_id} — Handle Delete a transaction 

## Fixed expenses / monthly cost

GET /fixed-expenses — Handle list the user's monthly cost
GET /fixed-expenses/{expense_id} — Handle list a expecific monthly cost
POST /fixed-expenses — Handle create a new expense
PATCH /fixed-expenses/{expense_id} — Handle Update a expense
DELETE /fixed-expenses/{expense_id} —Handle Delete a expense

## credit-installments

GET /credit-installments — Handle list the type = credit in the transactions and create a table that returns the installments that must be payed with interest calculated
GET /credit-installments/{transaction_id}  — handle a list of all installments to that transaction

## account-balances

GET /account-balances — Handle list the gains and expenses of transaction in each of accounts and return the balances.
GET /account-balances/{account_id}  — handle a list the balance of a expecific account

# when consult endpoints.md

When you need the schemas
Want to see the exemples of request/response complete
Is fixing a bug on a endpoint
Want to know the behavior of a endpoint
