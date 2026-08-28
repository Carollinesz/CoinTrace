import pytest

BASE = "/api/v1/transactions/credit-installments"
TRANSACTIONS_BASE = "/api/v1/transactions"
ACCOUNTS_BASE = "/api/v1/bank-accounts"


def _first_bank_id(client):
    return client.get("/api/v1/banks").json()[0]["bank_id"]


def _make_account(client):
    resp = client.post(ACCOUNTS_BASE, json={
        "bank_id": _first_bank_id(client),
        "account_name": "Test Account",
        "account_type": "checking",
        "start_value": 0.0,
    })
    return resp.json()["account_id"]


def _make_credit(client, account_id, installments=3):
    resp = client.post(TRANSACTIONS_BASE, json={
        "account_id": account_id,
        "transaction_date": "2024-01-15",
        "value": -900.0,
        "description": "TV",
        "type": "credit",
        "details": {
            "installments": installments,
            "first_payment": "2024-02-01",
            "interest": 0.0,
        },
    })
    return resp.json()


def test_list_empty(client):
    resp = client.get(BASE)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_installments(client):
    acc = _make_account(client)
    _make_credit(client, acc, installments=3)
    resp = client.get(BASE)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_list_installment_numbers_sequential(client):
    acc = _make_account(client)
    _make_credit(client, acc, installments=4)
    data = client.get(BASE).json()
    numbers = [item["installment_number"] for item in data]
    assert numbers == [1, 2, 3, 4]


def test_installment_value_no_interest(client):
    acc = _make_account(client)
    txn = _make_credit(client, acc, installments=4)
    data = [item for item in client.get(BASE).json()
            if item["transaction_id"] == txn["transaction_id"]]
    for item in data:
        assert float(item["installment_value"]) == pytest.approx(-225.0, rel=0.01)


def test_multiple_credit_transactions_listed(client):
    acc = _make_account(client)
    _make_credit(client, acc, installments=2)
    _make_credit(client, acc, installments=3)
    data = client.get(BASE).json()
    assert len(data) == 5


def test_list_filter_by_transaction_id(client):
    acc = _make_account(client)
    txn = _make_credit(client, acc, installments=2)
    _make_credit(client, acc, installments=3)
    data = client.get(f"{BASE}?transaction_id={txn['transaction_id']}").json()
    assert len(data) == 2
    assert {item["transaction_id"] for item in data} == {txn["transaction_id"]}


def test_list_filter_by_unknown_transaction_id_returns_empty(client):
    assert client.get(f"{BASE}?transaction_id=999999").json() == []
