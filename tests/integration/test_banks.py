BASE = "/api/v1/banks"


def test_list_banks_returns_seeded_data(client):
    resp = client.get(BASE)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "bank_id" in data[0]
    assert "bank_name" in data[0]


def test_list_banks_pagination(client):
    resp = client.get(f"{BASE}?skip=0&limit=3")
    assert resp.status_code == 200
    assert len(resp.json()) <= 3
