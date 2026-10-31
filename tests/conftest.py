import pytest


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    # 로컬 .env나 개발자의 실제 서비스 토큰이 테스트에 들어오지 않게 한다.
    from bonghwajigi.common.config import Settings

    for name in Settings.model_fields:
        monkeypatch.delenv(f"BONGHWA_{name.upper()}", raising=False)
    monkeypatch.setitem(Settings.model_config, "env_file", None)
