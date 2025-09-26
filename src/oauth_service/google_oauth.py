import os
import secrets
from typing import cast
from google.oauth2.credentials import Credentials
import google_auth_oauthlib.flow
from db.models import User, UserGoogleCredential, update_or_create_user


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


def authorize_oauth2(state: str | None) -> tuple[str, str]:
    """Returns authorization_url and state"""
    if state is None:
        state = secrets.token_urlsafe(32)
    # Required, call the from_client_secrets_file method to retrieve the client ID from a
    # client_secret.json file. The client ID (from that file) and access scopes are required. (You can
    # also use the from_client_config method, which passes the client configuration as it originally
    # appeared in a client secrets file but doesn't access the file itself.)
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
    )

    flow.redirect_uri = REDIRECT_URI

    # Generate URL for request to Google's OAuth 2.0 server.
    # Use kwargs to set optional request parameters.
    return flow.authorization_url(
        # Recommended, enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type="offline",
        state=state,
        # Optional, enable incremental authorization. Recommended as a best practice.
        include_granted_scopes="true",
        # Optional, set prompt to 'consent' will prompt the user for consent
        prompt="consent",
    )


def get_credentials(state: str, authorization_url: str, /, user: User | None = None) -> dict[str, str | list[str] | None]:
    flow = google_auth_oauthlib.flow.Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, state=state)
    flow.redirect_uri = REDIRECT_URI

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    flow.fetch_token(authorization_response=authorization_url)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials

    credentials = credentials_to_dict(cast(Credentials, credentials))

    if user:
        update_or_create_user(user)

    return credentials


def credentials_to_dict(credentials: Credentials | UserGoogleCredential) -> dict[str, str | list[str] | None]:
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "granted_scopes": credentials.granted_scopes,
    }


def check_granted_scopes(credentials: dict[str, str | None]):
    features = {}
    granted_scopes = credentials.get("granted_scopes")

    if not granted_scopes:
        return features

    features["email"] = "https://www.googleapis.com/auth/userinfo.email" in granted_scopes
    features["gmail"] = "https://www.googleapis.com/auth/gmail.readonly" in granted_scopes

    return features
