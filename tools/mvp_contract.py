"""배포되는 앱 API의 OpenAPI 스냅샷을 생성한다. 실제 비밀 설정이나 DB에 접근하지 않는다."""

import json
from pathlib import Path
from unittest.mock import patch

from bonghwajigi.api.app import create_app
from bonghwajigi.common.config import Settings


def main():
    settings = Settings(
        _env_file=None,
        analysis_enabled=True,
        policy_enabled=True,
        app_enabled=True,
        database_url="postgresql+psycopg://schema:unused@127.0.0.1:5432/schema",
        broker_url="redis://127.0.0.1:6379/15",
        service_token="schema-only-service",
        jwt_secret="schema-only-jwt-key-for-document-generation-123",
    )
    with patch("bonghwajigi.api.app.Settings", return_value=settings):
        app = create_app()
    output = Path("docs/V2/delivery/api/mvp-openapi.json")
    output.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n")
    app.state.sessions.kw["bind"].dispose()
    print("실행 API 명세 생성:", output)


if __name__ == "__main__":
    main()
