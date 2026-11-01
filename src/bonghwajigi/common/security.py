from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from bonghwajigi.common.config import Settings


def service_auth(settings: Settings):
    bearer = HTTPBearer(auto_error=False)

    def require_token(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ) -> None:
        expected = settings.service_token.get_secret_value() if settings.service_token else ""
        if not expected:
            raise HTTPException(status_code=503, detail="SERVICE_AUTH_NOT_CONFIGURED")
        if credentials is None or not compare_digest(
            credentials.credentials.encode(), expected.encode()
        ):
            raise HTTPException(
                status_code=401,
                detail="UNAUTHENTICATED",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return require_token
