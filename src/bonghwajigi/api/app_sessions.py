"""사설망 simulation 전용 설치 계정. 공개 운영 회원가입이 아니다."""

import hashlib
import hmac
import secrets
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import Field
from sqlalchemy import func, select

from bonghwajigi.api.user_auth import issue_token
from bonghwajigi.contracts.app import AppProfile, StoredInput, Strict
from bonghwajigi.contracts.mobile_output import Envelope
from bonghwajigi.contracts.policy import Identifier, ProfileInput
from bonghwajigi.db.analysis_models import new_id, now
from bonghwajigi.db.app_models import AppAccount, AppSession
from bonghwajigi.policy.service import put_entity, scope_lock
from bonghwajigi.policy.three_stage import bootstrap


class DemoConsent(Strict):
    version: Literal["internal-demo-v1"]
    service: Literal[True]
    privacy: Literal[True]
    location: Literal[True]


class InstallationRegistration(Strict):
    installation_id: Identifier
    consent: DemoConsent


class RefreshRequest(Strict):
    refresh_token: str = Field(min_length=70, max_length=256)


class SessionTokens(Strict):
    user_id: str
    scenario_id: str
    session_id: str
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int
    refresh_expires_at: str


def attach_app_sessions(app, settings, envelope):
    sessions = app.state.sessions
    router = APIRouter(prefix="/v1/auth", tags=["mobile-session"])

    def hash_token(value):
        return hashlib.sha256(value.encode()).hexdigest()

    def token_pair(row, secret):
        lifetime = min(settings.jwt_lifetime_seconds, 900)
        return SessionTokens(
            user_id=row.user_id,
            scenario_id=row.scenario_id,
            session_id=row.id,
            access_token=issue_token(
                settings,
                row.user_id,
                row.scenario_id,
                row.account_version,
                session_id=row.id,
                lifetime_seconds=lifetime,
            ),
            refresh_token=row.id + "." + secret,
            expires_in=lifetime,
            refresh_expires_at=row.expires_at.isoformat(),
        ).model_dump()

    @router.get("/config")
    def registration_config():
        return envelope(
            {
                "registration_enabled": settings.app_registration_enabled
                and settings.mode == "simulation",
                "consent_version": "internal-demo-v1",
                "kind": "private_simulation_installation",
                "notice": "내부 시연 서비스입니다. 실제 재난 경보·구조 접수 서비스가 아닙니다.",
            }
        )

    @router.post("/installations", status_code=201, response_model=Envelope[SessionTokens])
    def register(body: InstallationRegistration, request: Request):
        if not settings.app_registration_enabled or settings.mode != "simulation":
            raise HTTPException(404, detail="INSTALLATION_REGISTRATION_DISABLED")
        stamp = now()
        host = request.client.host if request.client else "unknown"
        client_digest = hmac.new(
            settings.jwt_secret.get_secret_value().encode(), host.encode(), hashlib.sha256
        ).hexdigest()
        with sessions.begin() as s:
            scope_lock(s, settings.app_registration_scenario)
            recent = s.scalar(
                select(func.count())
                .select_from(AppSession)
                .where(
                    AppSession.client_digest == client_digest,
                    AppSession.created_at >= stamp - timedelta(hours=1),
                )
            )
            if recent >= settings.app_registration_hourly_limit:
                raise HTTPException(
                    429, detail="REGISTRATION_RATE_LIMIT", headers={"Retry-After": "3600"}
                )
            scenario, user = settings.app_registration_scenario, "app-" + new_id()
            bootstrap(s, scenario, stamp)
            s.add(AppAccount(scenario_id=scenario, user_id=user, enabled=True, token_version=1))
            put_entity(s, scenario, "profile", user, ProfileInput(revision=1), user_id=user)
            put_entity(
                s,
                scenario,
                "app_profile",
                user,
                StoredInput(revision=1, data=AppProfile().model_dump()),
                user_id=user,
            )
            put_entity(
                s,
                scenario,
                "app_consent",
                user,
                StoredInput(
                    revision=1, data={**body.consent.model_dump(), "recorded_at": stamp.isoformat()}
                ),
            )
            secret = secrets.token_urlsafe(48)
            row = AppSession(
                id=new_id(),
                scenario_id=scenario,
                user_id=user,
                installation_id=body.installation_id,
                account_version=1,
                refresh_digest=hash_token(secret),
                client_digest=client_digest,
                created_at=stamp,
                expires_at=stamp + timedelta(seconds=settings.app_refresh_lifetime_seconds),
            )
            s.add(row)
            result = token_pair(row, secret)
        return envelope(result)

    @router.post("/refresh", response_model=Envelope[SessionTokens])
    def refresh(body: RefreshRequest):
        try:
            identifier, supplied = body.refresh_token.split(".", 1)
        except ValueError:
            raise HTTPException(401, detail="SESSION_INVALID") from None
        valid, result = False, None
        with sessions.begin() as s:
            row = s.scalar(select(AppSession).where(AppSession.id == identifier).with_for_update())
            if row is not None and row.revoked_at is None and row.expires_at > now():
                account = s.get(AppAccount, (row.scenario_id, row.user_id))
                if account and account.enabled and account.token_version == row.account_version:
                    valid = hmac.compare_digest(row.refresh_digest, hash_token(supplied))
                    if valid:
                        secret = secrets.token_urlsafe(48)
                        row.refresh_digest = hash_token(secret)
                        result = token_pair(row, secret)
                    else:
                        # 커밋 후 거부해 재사용 탐지에 따른 폐기가 rollback되지 않게 한다.
                        row.revoked_at = now()
        if not valid:
            raise HTTPException(401, detail="SESSION_INVALID")
        return envelope(result)

    app.include_router(router)
