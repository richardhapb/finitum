import json
import os
import secrets
from google.oauth2.credentials import Credentials
import google_auth_oauthlib.flow
from db.models import User, UserGoogleCredential, update_or_create_user
from redis import Redis


# Retrieve client ID and secret
CLIENT_ID = os.environ.get("GOOGLE_CLIENT")
CLIENT_SECRET = os.environ.get("GOOGLE_SECRET")
REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:9090/google_oauth2callback")

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",  # Access to user's email
    "https://www.googleapis.com/auth/gmail.readonly",  # Read-only access to Gmail
    "openid",  # Explicitly include OpenID scope if using OpenID Connect
]

CLIENT_CONFIG = {
    "web": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [REDIRECT_URI],
        # "javascript_origins": ["http://localhost:9090"],
    }
}


class OauthError(Exception):
    pass


class GoogleClient:
    _redirect_uri = REDIRECT_URI
    _scopes = SCOPES
    _config = CLIENT_CONFIG
    credentials: Credentials | UserGoogleCredential | None = None

    granted_scopes: dict[str, bool] = {}

    def __init__(self, credentials: Credentials | UserGoogleCredential | None = None):
        if isinstance(credentials, UserGoogleCredential) and not credentials.is_valid:
            credentials = None
        self.credentials = credentials

    def authorize_oauth2(self, state: str | None) -> tuple[str, str, str | None]:
        """Returns authorization_url, state, and PKCE code verifier."""
        if state is None:
            state = secrets.token_urlsafe(32)

        if not CLIENT_ID or not CLIENT_SECRET:
            raise OauthError("Missing GOOGLE_CLIENT/GOOGLE_SECRET")
        if not CLIENT_CONFIG["web"]["redirect_uris"]:
            raise OauthError("Redirect not found")
        if REDIRECT_URI not in CLIENT_CONFIG["web"]["redirect_uris"]:
            raise OauthError("Redirect not registered")

        # Required, call the from_client_secrets_file method to retrieve the client ID from a
        # client_secret.json file. The client ID (from that file) and access scopes are required. (You can
        # also use the from_client_config method, which passes the client configuration as it originally
        # appeared in a client secrets file but doesn't access the file itself.)
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            autogenerate_code_verifier=True,
        )

        flow.redirect_uri = self._redirect_uri

        # Generate URL for request to Google's OAuth 2.0 server.
        # Use kwargs to set optional request parameters.
        authorization_url, returned_state = flow.authorization_url(
            # Recommended, enable offline access so that you can refresh an access token without
            # re-prompting the user for permission. Recommended for web server apps.
            access_type="offline",
            state=state,
            # Optional, enable incremental authorization. Recommended as a best practice.
            include_granted_scopes="true",
            # Optional, set prompt to 'consent' will prompt the user for consent
            prompt="consent",
        )
        return authorization_url, returned_state, getattr(flow, "code_verifier", None)

    def get_credentials(
        self,
        state: str,
        authorization_url: str,
        /,
        *,
        code_verifier: str | None = None,
        user: User | None = None,
    ) -> dict[str, str | list[str] | None]:
        flow = google_auth_oauthlib.flow.Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, state=state)
        flow.redirect_uri = self._redirect_uri
        if code_verifier:
            flow.code_verifier = code_verifier

        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        flow.fetch_token(authorization_response=authorization_url)

        # Store credentials in the session.
        # ACTION ITEM: In a production app, you likely want to save these
        #              credentials in a persistent database instead.
        self.credentials = flow.credentials

        credentials_dict = self._credentials_to_dict()

        if user:
            update_or_create_user(user)

        return credentials_dict

    def _credentials_to_dict(self) -> dict[str, str | list[str] | None]:
        if not self.credentials:
            return {}

        expiry = getattr(self.credentials, "expiry", None)
        return {
            "token": self.credentials.token,
            "refresh_token": self.credentials.refresh_token,
            "token_uri": self.credentials.token_uri,
            "client_id": self._config["web"]["client_id"],
            "client_secret": self._config["web"]["client_secret"],
            "scopes": list(getattr(self.credentials, "scopes", []) or []),
            "granted_scopes": list(getattr(self.credentials, "granted_scopes", []) or []),
            "expiry": expiry.isoformat() if expiry else None,
            "id_token": getattr(self.credentials, "id_token", None),
            "account_email_hint": None,  # fill later if you decode id_token
        }

    def _check_granted_scopes(self, credentials: dict[str, str | None]) -> None:
        features = {}
        granted_scopes = credentials.get("granted_scopes")

        if not granted_scopes:
            return

        features["email"] = "https://www.googleapis.com/auth/userinfo.email" in granted_scopes
        features["gmail"] = "https://www.googleapis.com/auth/gmail.readonly" in granted_scopes

        self.granted_scopes = features


# Functions for state management
def generate_oauth_state() -> str:
    """Generate a unique OAuth state token."""
    state = secrets.token_urlsafe(32)
    return state


def store_oauth_state(redis_client: Redis, state: str, code_verifier: str | None) -> None:
    """Persist OAuth state metadata for the callback exchange."""
    payload = json.dumps({"code_verifier": code_verifier})
    redis_client.setex(f"oauth_state:{state}", 600, payload)


def consume_oauth_state(state: str, redis_client: Redis) -> dict[str, str | None] | None:
    """Load OAuth state metadata from Redis and delete it if valid."""
    key = f"oauth_state:{state}"
    raw_payload = redis_client.get(key)
    if raw_payload is None:
        return None

    redis_client.delete(key)

    if isinstance(raw_payload, bytes):
        raw_payload = raw_payload.decode("utf-8")

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        return {"code_verifier": None}

    if not isinstance(payload, dict):
        return {"code_verifier": None}

    code_verifier = payload.get("code_verifier")
    if code_verifier is not None and not isinstance(code_verifier, str):
        code_verifier = None

    return {"code_verifier": code_verifier}
