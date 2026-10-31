from datetime import timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from bonghwajigi.db.analysis_models import now
from bonghwajigi.db.app_models import AppAccount


def issue_token(settings, user, scenario, version=1):
    stamp = now()
    return jwt.encode(
        {
            "sub": user,
            "scenario_id": scenario,
            "token_version": version,
            "token_type": "access",
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": stamp,
            "nbf": stamp,
            "exp": stamp + timedelta(seconds=settings.jwt_lifetime_seconds),
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def user_auth(settings, sessions):
    if not settings.jwt_secret or len(settings.jwt_secret.get_secret_value()) < 32:
        raise RuntimeError("앱 인증에는 별도의 32바이트 이상 JWT 비밀키가 필요합니다.")
    if (
        settings.service_token
        and settings.jwt_secret.get_secret_value() == settings.service_token.get_secret_value()
    ):
        raise RuntimeError("앱 JWT 키와 내부 서비스 토큰을 분리하세요.")
    bearer = HTTPBearer(auto_error=False, scheme_name="UserJWT")

    def authenticate(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        try:
            if credentials is None or len(credentials.credentials) > 4096:
                raise ValueError
            claims = jwt.decode(
                credentials.credentials,
                settings.jwt_secret.get_secret_value(),
                algorithms=["HS256"],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
                options={
                    "require": [
                        "sub",
                        "scenario_id",
                        "exp",
                        "iat",
                        "nbf",
                        "token_type",
                        "token_version",
                    ]
                },
            )
            if claims["token_type"] != "access" or not isinstance(claims["scenario_id"], str):
                raise ValueError
            with sessions() as session:
                account = session.get(AppAccount, (claims["scenario_id"], claims["sub"]))
                if (
                    not account
                    or not account.enabled
                    or account.token_version != claims["token_version"]
                ):
                    raise ValueError
            return claims
        except (jwt.PyJWTError, ValueError, TypeError):
            raise HTTPException(
                401, detail="UNAUTHENTICATED", headers={"WWW-Authenticate": "Bearer"}
            ) from None

    return authenticate
