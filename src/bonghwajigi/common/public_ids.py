"""인증 조회와 알림 전송에서 공유하는 사용자 범위 공개 리소스 식별자."""

import hashlib
import hmac


def opaque_resource_id(secret, scenario, user, kind, identifier):
    if not secret:
        raise ValueError("공개 리소스 식별자 생성 키가 필요합니다.")
    content = ":".join((scenario, user, kind, identifier)).encode()
    return hmac.new(secret.encode(), content, hashlib.sha256).hexdigest()[:32]
