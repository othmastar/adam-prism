"""
[PHASE6] SSO (Single Sign-On) integration.
Supports OAuth2 / OIDC providers like Google, Microsoft, GitHub, Okta.

For local development, falls back to the simple credentials provider.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("adam_prism.auth.sso")


SUPPORTED_PROVIDERS = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scopes": ["openid", "email", "profile"],
    },
    "microsoft": {
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/oidc/userinfo",
        "scopes": ["openid", "email", "profile"],
    },
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scopes": ["read:user", "user:email"],
    },
    "okta": {
        "auth_url": None,  # Set per-tenant
        "token_url": None,
        "userinfo_url": None,
        "scopes": ["openid", "email", "profile"],
    },
    "keycloak": {
        "auth_url": None,  # Set per-deployment
        "token_url": None,
        "userinfo_url": None,
        "scopes": ["openid", "email", "profile"],
    },
    "auth0": {
        "auth_url": None,  # Set per-tenant
        "token_url": None,
        "userinfo_url": None,
        "scopes": ["openid", "email", "profile"],
    },
}


def get_oauth_config(provider: str) -> dict[str, Any] | None:
    """[PHASE6] Get OAuth2 config for a provider, with env var overrides."""
    if provider not in SUPPORTED_PROVIDERS:
        return None
    base = dict(SUPPORTED_PROVIDERS[provider])

    # Allow per-provider env override
    base["client_id"] = os.environ.get(f"ADAM_OAUTH_{provider.upper()}_CLIENT_ID")
    base["client_secret"] = os.environ.get(f"ADAM_OAUTH_{provider.upper()}_CLIENT_SECRET")
    base["redirect_uri"] = os.environ.get(
        f"ADAM_OAUTH_{provider.upper()}_REDIRECT_URI",
        f"http://localhost:8000/api/auth/sso/{provider}/callback",
    )

    # Okta, Keycloak, Auth0 need custom domain
    if provider in ("okta", "keycloak", "auth0"):
        domain = os.environ.get(f"ADAM_OAUTH_{provider.upper()}_DOMAIN")
        if domain:
            base["auth_url"] = f"https://{domain}/oauth2/authorize"
            base["token_url"] = f"https://{domain}/oauth2/token"
            base["userinfo_url"] = f"https://{domain}/oauth2/userinfo"
        else:
            logger.warning(
                f"[SSO] {provider} requires ADAM_OAUTH_{provider.upper()}_DOMAIN"
            )
            return None

    if not base.get("client_id"):
        logger.debug(f"[SSO] {provider} not configured (missing client_id)")
        return None
    return base


def list_configured_providers() -> list[str]:
    """[PHASE6] List all SSO providers that have valid configuration."""
    configured = []
    for provider in SUPPORTED_PROVIDERS:
        if get_oauth_config(provider):
            configured.append(provider)
    return configured


async def exchange_code_for_token(
    provider: str, code: str, redirect_uri: str
) -> dict[str, Any] | None:
    """[PHASE6] Exchange OAuth2 authorization code for access token."""
    import httpx

    config = get_oauth_config(provider)
    if not config:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                config["token_url"],
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                },
            )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.error(f"[SSO] Token exchange failed for {provider}: {e}")
    return None


async def get_user_info(provider: str, access_token: str) -> dict[str, Any] | None:
    """[PHASE6] Get user info from OAuth2 provider."""
    import httpx

    config = get_oauth_config(provider)
    if not config:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                config["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.error(f"[SSO] User info failed for {provider}: {e}")
    return None
