import pytest

BASE = "/api/v1/bank-accounts"


def _first_bank_id(client):
    return client.get("/api/v1/banks").json()[0]["bank_id"]


def _create(client, name="Conta Teste", account_type="checking", start_value=1000.0):
    return client.post(BASE, json={
        "bank_id": _first_bank_id(client),
        "account_name": name,
        "account_type": account_type,
        "start_value": start_value,
    })


# ── List ──────────────────────────────────────────────────────────────────────

def test_list_empty(client):
    resp = client.get(BASE)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_returns_created_accounts(client):
    _create(client, name="Alpha")
    _create(client, name="Beta")
    names = [a["account_name"] for a in client.get(BASE).json()]
    assert "Alpha" in names
    assert "Beta" in names


def test_list_pagination(client):
    for i in range(5):
        _create(client, name=f"Conta {i}")
    resp = client.get(f"{BASE}?limit=3")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


# ── Create ────────────────────────────────────────────────────────────────────

def test_create_success(client):
    resp = _create(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["account_name"] == "Conta Teste"
    assert data["account_type"] == "checking"
    assert float(data["start_value"]) == 1000.0
    assert "account_id" in data


def test_create_duplicate_name_returns_409(client):
    _create(client, name="Duplicada")
    resp = _create(client, name="Duplicada")
    assert resp.status_code == 409


# ── Update ────────────────────────────────────────────────────────────────────

def test_update_name(client):
    created = _create(client).json()
    resp = client.patch(f"{BASE}/{created['account_id']}", json={"account_name": "Novo Nome"})
    assert resp.status_code == 200
    assert resp.json()["account_name"] == "Novo Nome"


def test_update_start_value(client):
    created = _create(client).json()
    resp = client.patch(f"{BASE}/{created['account_id']}", json={"start_value": 500.0})
    assert resp.status_code == 200
    assert float(resp.json()["start_value"]) == 500.0


def test_update_name_to_existing_returns_409(client):
    _create(client, name="Conta Um")
    b = _create(client, name="Conta Dois").json()
    resp = client.patch(f"{BASE}/{b['account_id']}", json={"account_name": "Conta Um"})
    assert resp.status_code == 409


def test_update_not_found(client):
    assert client.patch(f"{BASE}/999999", json={"account_name": "X"}).status_code == 404


# ── Delete ────────────────────────────────────────────────────────────────────

def test_delete_success(client):
    created = _create(client).json()
    assert client.delete(f"{BASE}/{created['account_id']}").status_code == 204
    assert client.get(f"{BASE}/{created['account_id']}").status_code == 404


def test_delete_not_found(client):
    assert client.delete(f"{BASE}/999999").status_code == 404
