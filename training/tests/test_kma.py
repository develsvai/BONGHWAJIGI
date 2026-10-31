import urllib.error

import pytest

from bonghwa_training.kma_download import acquire_one, load_key, validate_original


def test_private_key_file_is_data_not_shell(tmp_path, monkeypatch):
    monkeypatch.delenv("KMA_APIHUB_AUTH_KEY", raising=False)
    p = tmp_path / "training.env"
    p.write_text('KMA_APIHUB_AUTH_KEY="literal$(not-executed)"\n')
    p.chmod(0o600)
    assert load_key(p) == "literal$(not-executed)"
    p.chmod(0o644)
    with pytest.raises(ValueError, match="600"):
        load_key(p)


def test_html_auth_error_is_not_valid_netcdf(tmp_path):
    p = tmp_path / "bad.part"
    p.write_bytes(b"<html>permission denied</html>")
    with pytest.raises(ValueError, match="NetCDF"):
        validate_original(p)


def test_http_error_does_not_expose_auth_url_or_body(tmp_path, monkeypatch):
    from datetime import UTC, datetime

    def fail(url, **kwargs):
        raise urllib.error.HTTPError(url, 403, "secret-token", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", fail)
    with pytest.raises(RuntimeError) as caught:
        acquire_one(tmp_path, datetime(2022, 3, 4, tzinfo=UTC), "secret-token")
    assert "403" in str(caught.value)
    assert "secret-token" not in str(caught.value)
    assert not list(tmp_path.glob("*.nc"))
