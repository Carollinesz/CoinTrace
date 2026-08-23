# financial-api — Endpoint Reference

Base URL: `/api/v1` | Version: `0.1.0`

## Table of Contents
- [Bank Accounts](#bank-accounts)
  - [GET /bank-accounts](#get-bank-accounts)
  - [POST /bank-accounts](#post-bank-accounts)
  - [GET /bank-accounts/{account_id}](#get-bank-accountsaccount_id)
  - [PATCH /bank-accounts/{account_id}](#patch-bank-accountsaccount_id)
  - [DELETE /bank-accounts/{account_id}](#delete-bank-accountsaccount_id)
- [Banks](#banks)
  - [GET /banks](#get-banks)
  - [GET /banks/{bank_id}](#get-banksbank_id)
- [Transactions](#transactions)
  - [GET /transactions](#get-transactions)
  - [POST /transactions](#post-transactions)
  - [GET /transactions/{transaction_id}](#get-transactionstransaction_id)
  - [PATCH /transactions/{transaction_id}](#patch-transactionstransaction_id)
  - [DELETE /transactions/{transaction_id}](#delete-transactionstransaction_id)
  - [POST /transactions/upload](#post-transactionsupload)
- [Fixed Expenses](#fixed-expenses)
  - [GET /fixed-expenses](#get-fixed-expenses)
  - [POST /fixed-expenses](#post-fixed-expenses)
  - [GET /fixed-expenses/{expense_id}](#get-fixed-expensesexpense_id)
  - [PATCH /fixed-expenses/{expense_id}](#patch-fixed-expensesexpense_id)
  - [DELETE /fixed-expenses/{expense_id}](#delete-fixed-expensesexpense_id)
- [Credit Installments](#credit-installments)
  - [GET /credit-installments](#get-credit-installments)
  - [GET /credit-installments/{transaction_id}](#get-credit-installmentstransaction_id)
- [Account Balances](#account-balances)
  - [GET /account-balances](#get-account-balances)
  - [GET /account-balances/{account_id}](#get-account-balancesaccount_id)
- [Health](#health)

> **Validation errors (422)** — All endpoints that accept input return `422` on invalid data. Response shape:
> ```json
> {
>   "detail": [
>     { "loc": ["body", "field_name"], "msg": "error message", "type": "error_type" }
>   ]
> }
> ```

---

## Bank Accounts

### GET /bank-accounts

List all bank accounts.

**Query params:**
| Param | Type | Required | Default | Notes |
|---|---|---|---|---|
| `skip` | integer | no | 0 | Offset for pagination (min: 0) |
| `limit` | integer | no | 100 | Max items to return (min: 1, max: 500) |

**Response 200** — array of bank accounts:
```json
[
  {
    "account_id": 1,
    "bank_id": 3,
    "account_name": "Main Checking",
    "account_type": "checking",
    "start_value": 1500.00
  }
]
```

---

### POST /bank-accounts

Create a new bank account.

**Body** (required fields marked with *):
```json
{
  "bank_id": 3,                    // * integer — ID of the bank
  "account_name": "Main Checking", // * string unique
  "account_type": "checking",      // * string 
  "start_value": 1500.00           // number — initial balance (default: 0.0)
}
```

**Response 201:**
```json
{
  "account_id": 1,
  "bank_id": 3,
  "account_name": "Main Checking",
  "account_type": "checking",
  "start_value": 1500.00
}
```

---

### GET /bank-accounts/{account_id}

Retrieve a single bank account by ID.

**Path param:** `account_id` (integer, required)

**Response 200:** single bank account object (same shape as POST 201)

---

### PATCH /bank-accounts/{account_id}

Partially update a bank account. Send only the fields you want to change.

**Path param:** `account_id` (integer, required)

**Body** (all fields optional):
```json
{
  "account_name": "Personal Savings",
  "account_type": "savings",
  "start_value": 2000.00
}
```

**Response 200:** updated bank account object

---

### DELETE /bank-accounts/{account_id}

Delete a bank account.

**Path param:** `account_id` (integer, required)

**Response 204:** no body

---

## Banks

### GET /banks

List all available banks. When a user creates a new account, he must choose one of these banks to associate the account.

**Query params:** `skip` (default: 0) and `limit` (default: 100, max: 500)

**Response 200:**
```json
[
  { "bank_id": 1, "bank_name": "Nubank" },
  { "bank_id": 2, "bank_name": "Itaú" }
]
```

---

### GET /banks/{bank_id}

Retrieve a single bank by ID.

**Path param:** `bank_id` (integer, required)

**Response 200:**
```json
{ "bank_id": 1, "bank_name": "Nubank" }
```

---

## Transactions

### GET /transactions

List all transactions.

**Query para_ms:** `skip` (default: 0), `limit` (default: 100, max: 500), `account_id` (integer | null), `type` (string | null), `category` (string | null), `tracking` (boolean | null), `date_from` (string | null)($date), `date_to` (string | null)($date)

**Response 200** — array of transactions:
```json
[
  {
    "transaction_id": 10,
    "account_id": 1,
    "transaction_date": "2024-03-15",
    "value": "-149.90",
    "description": "Supermarket",
    "category": "Food",
    "type": "debit",
    "details": null, // JSONB dict on postgreesql
    "tracking": true,
    "created_at": "2024-03-15T18:00:00"
  }
]
```

> **Note on `value`:** returned as a string with up to 2 decimal places. Negative = expense, positive = income.
> **Note on `details`:** all credit transactions has a dict with 3 values: first_payment (a Date when the first installment must be payed), installments(integer, the number of months that will have a installment), interest(float, the interest rate that increses every installment)

---

### POST /transactions

Create a new transaction.

**Body** (required fields marked with *):
```json
{
  "transaction_date": "2024-03-15",     // * string (YYYY-MM-DD)
  "value": -149.90,                     // * number or string — negative = expense, positive = income
  "description": "Supermarket",         // * string
  "account_id": 1,                      // integer | null (default: 0)
  "category": "Food",                   // string | null
  "type": "debit",                      // string | null — e.g. "debit", "credit" (default: "debit")
  "details": { 
    "first_payment": "weekly shop",
    "installments": 12,
    "interest": 0.0
  }, // object | null — free-form extra data
  "tracking": true                      // boolean (default: true)
}
```

> **Note on `details`:** all credit transactions has a dict with 3 values: first_payment (a Date when the first installment must be payed), installments(integer, the number of months that will have a installment), interest(float, the interest rate that increses every installment) first_payment is not null, but interest and installments has the default value = 0 and 0.0

**Response 201:** created transaction object (same shape as GET /transactions item)

---

### GET /transactions/{transaction_id}

Retrieve a single transaction by ID.

**Path param:** `transaction_id` (integer, required)

**Response 200:** single transaction object

---

### PATCH /transactions/{transaction_id}

Partially update a transaction. Send only the fields you want to change.

**Path param:** `transaction_id` (integer, required)

**Body** (all fields optional):
```json
{
  "account_id": 2,
  "transaction_date": "2024-03-16",
  "value": -200.00,
  "description": "Updated description",
  "category": "Groceries",
  "tracking": false
}
```
**Response 200:** updated transaction object

> **Note:** the file must be the following REQUIRED COLUMNS {"transaction_date", "value", "description"} and the following option columns {"accountid_id", "category", "tracking"}, if not have the optional columns the default values it will be applied
---

### DELETE /transactions/{transaction_id}

Delete a transaction.

**Path param:** `transaction_id` (integer, required)

**Response 204:** no body

---

### POST /transactions/upload

Bulk-import transactions from a file (only xlsx, xls, ofx is accepted).

**Content-Type:** `multipart/form-data`

**Form field:**
| Field | Type | Required |
|---|---|---|
| `file` | binary (file upload) | yes |
| `account_id` | int | yes |
| `tracking` | bool | no |


**Response 200:**
```json
{
  "created": 42,
  "errors": [
    { "errors": { "row": 5, "detail": "missing required field: description" } }
  ]
}
```

- `created` — number of successfully imported transactions
- `errors` — array of row-level errors; empty array if all rows succeeded

---

## Fixed Expenses

Recurring monthly expenses with a fixed due day.

### GET /fixed-expenses

List all fixed expenses.

**Query params:** `skip` (default: 0) and `limit` (default: 100, max: 500)

**Response 200:**
```json
[
  {
    "expense_id": 5,
    "name": "Internet",
    "value": "129.90",
    "due_day": 10,
    "category": "Utilities",
    "account_id": 1,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

---

### POST /fixed-expenses

Create a new fixed expense.

**Body** (required fields marked with *):
```json
{
  "name": "Internet",       // * string
  "value": 129.90,          // * number or string — amount of the expense
  "due_day": 10,            // * integer — day of month it's due (1–31)
  "category": "Utilities",  // string | null (default: "Outros")
  "account_id": 1,          // integer | null — linked bank account
  "is_active": true         // boolean (default: true)
}
```

**Response 201:** created fixed expense object (same shape as GET /fixed-expenses item)

---

### GET /fixed-expenses/{expense_id}

Retrieve a single fixed expense by ID.

**Path param:** `expense_id` (integer, required)

**Response 200:** single fixed expense object

---

### PATCH /fixed-expenses/{expense_id}

Partially update a fixed expense.

**Path param:** `expense_id` (integer, required)

**Body** (all fields optional):
```json
{
  "name": "Home Internet",
  "value": 149.90,
  "due_day": 15,
  "category": "Utilities",
  "account_id": 2,
  "is_active": false
}
```

**Response 200:** updated fixed expense object

---

### DELETE /fixed-expenses/{expense_id}

Delete a fixed expense.

**Path param:** `expense_id` (integer, required)

**Response 204:** no body

---

## Credit Installments

Read-only. Installments are derived from transactions recorded as credit purchases split into multiple payments.

### GET /credit-installments

List all credit installments.

**Query params:** `skip` (default: 0), `limit` (default: 100, max: 500), `account_id` integer | null, `category` string | null, `due_date_from` string | (string | null)($date) and `due_date_to` string | (string | null)($date)

**Response 200:**
```json
[
  {
    "transaction_id": 10,
    "account_id": 1,
    "description": "New laptop",
    "category": "Electronics",
    "transaction_date": "2024-01-10",
    "total_value": "3600.00",
    "total_installments": 12,
    "installment_number": 3,
    "due_date": "2024-03-10",
    "interest_rate": "0.00",
    "installment_value": "300.00"
  }
]
```

---

### GET /credit-installments/{transaction_id}

Retrieve all installments for a specific transaction.

**Path param:** `transaction_id` (integer, required)

**Response 200:** array of installment objects (same shape as above) — all installments for that transaction

---

## Account Balances

Read-only computed balances. Returns all accounts without pagination.

### GET /account-balances

List computed balances for all bank accounts.

**Response 200:**
```json
[
  {
    "account_id": 1,
    "account_name": "Main Checking",
    "account_type": "checking",
    "start_value": "1500.00",
    "total_gains": "5200.00",
    "total_expenses": "-3800.00",
    "current_balance": "2900.00"
  }
]
```

- `start_value` — initial balance set when account was created
- `total_gains` — sum of all positive transactions 
- `total_expenses` — sum of all negative transactions
- `current_balance` — computed as `start_value + total_gains + total_expenses`

> All monetary fields are returned as strings with 2 decimal places.

---

### GET /account-balances/{account_id}

Retrieve the computed balance for a single account.

**Path param:** `account_id` (integer, required)

**Response 200:** single balance object (same shape as above)

---

## Health

### GET /health

Check if the API is running. No auth required.

**Response 200:** `{}` — empty object; presence of 200 confirms the service is healthy