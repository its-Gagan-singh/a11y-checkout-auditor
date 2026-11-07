from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_audit_rejects_private_addresses():
    r = client.post("/audit", json={"url": "http://127.0.0.1:9999"})
    assert r.status_code == 400


def test_audit_rejects_non_urls():
    assert client.post("/audit", json={"url": "not a url"}).status_code == 422


def test_dashboard_is_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "Checkout Auditor" in r.text
