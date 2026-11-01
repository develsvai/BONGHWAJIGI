"""사설망 시연 계정을 발급한다. 토큰은 화면 대신 권한 600의 파일에만 기록한다."""

import argparse
import json
import os
from pathlib import Path

from pydantic import TypeAdapter

from bonghwajigi.api.user_auth import issue_token
from bonghwajigi.common.config import Settings
from bonghwajigi.contracts.app import AppProfile, StoredInput
from bonghwajigi.contracts.policy import Identifier, ProfileInput
from bonghwajigi.db.app_models import AppAccount
from bonghwajigi.db.policy_models import PolicyEntity
from bonghwajigi.db.session import session_factory
from bonghwajigi.policy.service import put_entity, scope_lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument(
        "--mobility",
        choices=["independent", "walking_aid", "assistance_required"],
        default="independent",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for value in (args.scenario, args.user):
        TypeAdapter(Identifier).validate_python(value)
    settings = Settings()
    if (
        settings.mode != "simulation"
        or not settings.jwt_secret
        or len(settings.jwt_secret.get_secret_value()) < 32
    ):
        parser.exit(2, "simulation 모드와 별도 JWT 비밀키를 설정하세요.\n")
    if args.output.exists():
        parser.exit(2, "기존 토큰 파일을 덮어쓰지 않습니다. 새 출력 경로를 지정하세요.\n")
    sessions = session_factory(settings)
    with sessions.begin() as session:
        scope_lock(session, args.scenario)
        account = session.get(AppAccount, (args.scenario, args.user))
        if account is None:
            account = AppAccount(scenario_id=args.scenario, user_id=args.user, token_version=1)
            session.add(account)
        account.enabled = True
        for kind in ("profile", "app_profile"):
            if session.get(PolicyEntity, (args.scenario, kind, args.user)) is not None:
                continue
            if kind == "app_profile":
                payload = StoredInput(
                    revision=1, data=AppProfile(mobility=args.mobility).model_dump(mode="json")
                )
            else:
                mobility = {
                    "independent": "independent",
                    "walking_aid": "needs_time",
                    "assistance_required": "requires_help",
                }[args.mobility]
                payload = ProfileInput(
                    revision=1, mobility=mobility, mobility_assistance=mobility != "independent"
                )
            put_entity(session, args.scenario, kind, args.user, payload, user_id=args.user)
        token = issue_token(settings, args.user, args.scenario, account.token_version)
    args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(
            {
                "user_id": args.user,
                "scenario_id": args.scenario,
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": settings.jwt_lifetime_seconds,
            },
            stream,
            indent=2,
        )
        stream.write("\n")
    sessions.kw["bind"].dispose()
    print("시연 계정 파일 저장:", args.output)


if __name__ == "__main__":
    main()
