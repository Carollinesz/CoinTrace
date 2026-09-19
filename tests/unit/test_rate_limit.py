from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import rate_limit
from app.core.rate_limit import RateLimitMiddleware


def build_client(limit_per_minute: int) -> TestClient:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limit_per_minute=limit_per_minute)

    @app.get("/ping")
    def handle_ping():
        return {"ok": True}

    @app.get("/health")
    def handle_health():
        return {"status": "ok"}

    return TestClient(app)


def test_allows_requests_up_to_the_limit():
    client = build_client(limit_per_minute=3)

    statuses = [client.get("/ping").status_code for _ in range(3)]

    assert statuses == [200, 200, 200]


def test_blocks_requests_over_the_limit_with_retry_after():
    client = build_client(limit_per_minute=2)
    client.get("/ping")
    client.get("/ping")

    response = client.get("/ping")

    assert response.status_code == 429
    assert response.json() == {"message": "Too many requests, try again later"}
    assert 1 <= int(response.headers["Retry-After"]) <= 60


def test_resets_after_the_window(monkeypatch):
    clock = {"now": 1000.0}
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: clock["now"])
    client = build_client(limit_per_minute=1)
    client.get("/ping")
    assert client.get("/ping").status_code == 429

    clock["now"] += rate_limit.WINDOW_SECONDS

    assert client.get("/ping").status_code == 200


def test_health_is_never_limited():
    client = build_client(limit_per_minute=1)

    statuses = [client.get("/health").status_code for _ in range(5)]

    assert statuses == [200] * 5


def test_zero_disables_the_limit():
    client = build_client(limit_per_minute=0)

    statuses = [client.get("/ping").status_code for _ in range(10)]

    assert statuses == [200] * 10
