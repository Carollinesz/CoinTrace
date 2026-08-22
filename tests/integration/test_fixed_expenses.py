BASE = "/api/v1/fixed-expenses"
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


def _expense(name="Netflix", value=55.90, due_day=5, account_id=None):
    payload = {"name": name, "value": value, "due_day": due_day,
               "category": "Assinaturas", "is_active": True}
    if account_id is not None:
        payload["account_id"] = account_id
    return payload


# ── List ──────────────────────────────────────────────────────────────────────

def test_list_empty(client):
    assert client.get(BASE).json() == []


def test_list_returns_created(client):
    client.post(BASE, json=_expense("Netflix"))
    client.post(BASE, json=_expense("Spotify"))
    names = [e["name"] for e in client.get(BASE).json()]
    assert "Netflix" in names
    assert "Spotify" in names


# ── Create ────────────────────────────────────────────────────────────────────

def test_create_success(client):
    resp = client.post(BASE, json=_expense())
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Netflix"
    assert data["due_day"] == 5
    assert "expense_id" in data


def test_create_with_account(client):
    acc = _make_account(client)
    resp = client.post(BASE, json=_expense(account_id=acc))
    assert resp.status_code == 201
    assert resp.json()["account_id"] == acc


def test_create_with_nonexistent_account_returns_404(client):
    assert client.post(BASE, json=_expense(account_id=999999)).status_code == 404


def test_create_invalid_due_day_returns_422(client):
    assert client.post(BASE, json=_expense(due_day=32)).status_code == 422


def test_create_due_day_zero_returns_422(client):
    assert client.post(BASE, json=_expense(due_day=0)).status_code == 422


# ── Update ────────────────────────────────────────────────────────────────────

def test_update_value_and_active(client):
    created = client.post(BASE, json=_expense()).json()
    resp = client.patch(f"{BASE}/{created['expense_id']}", json={"value": 75.0, "is_active": False})
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["value"]) == 75.0
    assert data["is_active"] is False


def test_update_due_day(client):
    created = client.post(BASE, json=_expense()).json()
    resp = client.patch(f"{BASE}/{created['expense_id']}", json={"due_day": 10})
    assert resp.status_code == 200
    assert resp.json()["due_day"] == 10


def test_update_to_nonexistent_account_returns_404(client):
    created = client.post(BASE, json=_expense()).json()
    resp = client.patch(f"{BASE}/{created['expense_id']}", json={"account_id": 999999})
    assert resp.status_code == 404


def test_update_not_found(client):
    assert client.patch(f"{BASE}/999999", json={"name": "X"}).status_code == 404


# ── Delete ────────────────────────────────────────────────────────────────────

def test_delete_success(client):
    created = client.post(BASE, json=_expense()).json()
    assert client.delete(f"{BASE}/{created['expense_id']}").status_code == 204
    assert client.get(f"{BASE}/{created['expense_id']}").status_code == 404


def test_delete_not_found(client):
    assert client.delete(f"{BASE}/999999").status_code == 404
