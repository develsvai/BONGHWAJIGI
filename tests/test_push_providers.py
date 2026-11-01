import json

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from bonghwajigi.notifications.providers import FcmSender, PushError


@pytest.fixture
def credential(tmp_path):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    path = tmp_path / "test-service-account.json"
    path.write_text(
        json.dumps(
            {
                "type": "service_account",
                "client_email": "test@example.invalid",
                "private_key": private.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                ).decode(),
            }
        )
    )
    path.chmod(0o600)
    return path


@pytest.mark.parametrize(
    ("status", "code", "retryable", "unregister"),
    [
        (429, "QUOTA_EXCEEDED", True, False),
        (503, "UNAVAILABLE", True, False),
        (404, "UNREGISTERED", False, True),
        (400, "INVALID_ARGUMENT", False, False),
    ],
)
def test_provider_errors_are_distinct_from_delivery(
    credential, status, code, retryable, unregister
):
    calls = []

    def handler(request):
        calls.append(request.url.host)
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "test-access", "expires_in": 3600})
        assert request.url.host == "fcm.googleapis.com"
        return httpx.Response(status, json={"error": {"details": [{"errorCode": code}]}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    sender = FcmSender("test-project", credential, client)
    with pytest.raises(PushError) as caught:
        sender.send("test-device", {"resource_id": "fire"}, "urgent")
    assert caught.value.retryable is retryable
    assert caught.value.unregister is unregister
    assert "test-access" not in str(caught.value)
    assert calls == ["oauth2.googleapis.com", "fcm.googleapis.com"]
    client.close()


def test_provider_acceptance_is_not_device_receipt_and_credentials_are_private(credential):
    def handler(request):
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "test-access", "expires_in": 3600})
        message = json.loads(request.content)["message"]
        assert "latitude" not in str(message)
        assert message["android"]["priority"] == "high"
        return httpx.Response(200, json={"name": "projects/test-project/messages/accepted"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        sender = FcmSender("test-project", credential, client)
        assert sender.send("test-device", {"revision": "2"}, "high")[0] == "provider_accepted"
        credential.chmod(0o644)
        with pytest.raises(PushError, match="PERMISSIONS"):
            FcmSender("test-project", credential, client)
