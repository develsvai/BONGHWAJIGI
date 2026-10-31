import json
import re
import time

import httpx
import jwt


class PushError(Exception):
    def __init__(self, code, *, retryable=False, unregister=False):
        self.code, self.retryable, self.unregister = code, retryable, unregister
        super().__init__(code)


class SimulationSender:
    def send(self, token, payload, urgency):
        return "simulated", "simulation-only"


class DisabledSender:
    def send(self, token, payload, urgency):
        raise PushError("PUSH_NOT_CONFIGURED")


class FcmSender:
    def __init__(self, project, credentials_file, client=None):
        if not project or not re.fullmatch(r"[a-z][a-z0-9-]{4,62}", project):
            raise PushError("FCM_PROJECT_NOT_CONFIGURED")
        if not credentials_file or credentials_file.stat().st_mode & 0o077:
            raise PushError("FCM_CREDENTIAL_PERMISSIONS")
        self.project, self.credentials = project, json.loads(credentials_file.read_text())
        if self.credentials.get("type") != "service_account":
            raise PushError("FCM_CREDENTIAL_TYPE")
        self.client = client or httpx.Client(timeout=10, follow_redirects=False)
        self.token, self.until = None, 0

    def access_token(self):
        if time.time() + 60 < self.until:
            return self.token
        stamp = int(time.time())
        assertion = jwt.encode(
            {
                "iss": self.credentials["client_email"],
                "scope": "https://www.googleapis.com/auth/firebase.messaging",
                "aud": "https://oauth2.googleapis.com/token",
                "iat": stamp,
                "exp": stamp + 3600,
            },
            self.credentials["private_key"],
            algorithm="RS256",
        )
        response = self.client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
        )
        if response.status_code != 200:
            raise PushError("FCM_AUTH_FAILED", retryable=response.status_code >= 500)
        result = response.json()
        self.token, self.until = result["access_token"], time.time() + int(result["expires_in"])
        return self.token

    def send(self, token, payload, urgency):
        try:
            response = self.client.post(
                f"https://fcm.googleapis.com/v1/projects/{self.project}/messages:send",
                headers={"Authorization": "Bearer " + self.access_token()},
                json={
                    "message": {
                        "token": token,
                        "data": payload,
                        "notification": {
                            "title": "봉화지기 안내",
                            "body": "새로운 재난 안내를 확인하세요.",
                        },
                        "android": {
                            "priority": "high" if urgency in {"high", "urgent"} else "normal"
                        },
                    }
                },
            )
            if response.status_code == 200:
                return "provider_accepted", response.json()["name"]
            result = response.json().get("error", {})
            unregistered = any(
                d.get("errorCode") == "UNREGISTERED" for d in result.get("details", [])
            )
            raise PushError(
                "FCM_UNREGISTERED" if unregistered else "FCM_REJECTED",
                retryable=response.status_code in {429, 500, 502, 503, 504},
                unregister=unregistered,
            )
        except httpx.HTTPError:
            # 불확실한 수신 이후 재전송될 수 있다. 앱은 resource/revision으로 중복을 억제한다.
            raise PushError("FCM_NETWORK_UNCERTAIN", retryable=True) from None


def configured_sender(settings):
    if not settings.notifications_enabled or settings.push_provider == "disabled":
        return DisabledSender()
    if settings.push_provider == "simulation":
        return SimulationSender()
    return FcmSender(settings.fcm_project_id, settings.fcm_credentials_file)
