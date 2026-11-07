import pytest

from backend.app.security import is_public_url


@pytest.fixture(autouse=True)
def _no_override(monkeypatch):
    monkeypatch.delenv("ALLOW_PRIVATE_URLS", raising=False)


@pytest.mark.parametrize("url", [
    "http://127.0.0.1:8000",
    "http://localhost/admin",
    "http://10.0.0.5/",
    "http://192.168.1.1/",
    "http://169.254.169.254/latest/meta-data",
    "ftp://example.com/file",
])
def test_private_or_invalid_urls_are_blocked(url):
    assert is_public_url(url) is False


def test_override_allows_private(monkeypatch):
    monkeypatch.setenv("ALLOW_PRIVATE_URLS", "1")
    assert is_public_url("http://127.0.0.1:8000") is True
